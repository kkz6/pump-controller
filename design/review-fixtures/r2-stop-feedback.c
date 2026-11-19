/*
 * Offline feedback-fault audit of panel_controls_step, without a connected motor.
 * From the repository root:
 *   cc -std=c11 -Wall -Wextra -Werror -Ifirmware/components/starter_outputs/include \
 *      design/review-fixtures/r2-stop-feedback.c \
 *      firmware/components/starter_outputs/{starter_outputs,panel_controls}.c \
 *      -o /tmp/r2-stop-feedback && /tmp/r2-stop-feedback
 * An exit status of 1 means at least one hazardous response was observed.
 */
#include "panel_controls.h"

#include <assert.h>
#include <stdio.h>

enum { B_START_N = 1, B_SET_N = 2, B_STOP_OK = 4, B_MODE = 8,
       B_GUARD_OK = 32, B_MAN_N = 64, A_AUTO_N = 1, A_LOCAL_N = 4 };

struct fixture {
    struct panel_controls panel;
    struct panel_sample sample;
    uint32_t now;
};

static struct panel_result tick(struct fixture *f, uint32_t ms)
{
    f->now += ms;
    f->sample.sampled_at_ms = f->sample.protection_checked_at_ms = f->now;
    return panel_controls_step(&f->panel, f->now, f->sample);
}

static void settle_guard(struct fixture *f)
{
    for (unsigned i = 0; i < GUARD_QUIET_MS + 100; i += 10) tick(f, 10);
    assert(f->panel.guard_recovered);
}

static void setup(struct fixture *f, enum starter_profile profile)
{
    struct starter_config config = {
        .profile = profile, .harness_profile = profile, .independent_shutdown = true,
        .start_range={5,100}, .stop_range={5,100}, .confirm_stop_ms=150,
        .contact_settle_ms = 5, .start_pulse_ms = 10, .stop_pulse_ms = 10
    };
    assert(panel_controls_configure(&f->panel, config, false, 4, 20));
    f->sample = (struct panel_sample){
        .gpio_a = A_LOCAL_N | A_AUTO_N,
        .gpio_b = B_START_N | B_SET_N | B_STOP_OK | B_GUARD_OK | B_MAN_N,
        .valid = true, .process_healthy = true, .motor_stopped = true
    };
    tick(f, 0);
    settle_guard(f);
}

static void arm_from_front_panel(struct fixture *f)
{
    f->sample.gpio_b &= (uint8_t)~B_START_N;
    tick(f, 1);
    assert(tick(f, 4).drive.arm_issued);
}

static bool ignored_stop(void)
{
    struct fixture f = {0};
    setup(&f, STARTER_PULSE_STOP);
    f.sample.fill_demand = true;
    f.sample.gpio_b |= B_MODE;
    tick(&f, 1);
    assert(tick(&f, 5).mode == PANEL_AUTO);
    f.sample.gpio_b &= (uint8_t)~B_MODE;
    settle_guard(&f);
    arm_from_front_panel(&f);
    assert(tick(&f, 1).drive.start_issued);
    f.sample.motor_stopped = false;  /* Simulated motor starts. */
    f.sample.gpio_b |= B_START_N;
    tick(&f, 1);
    tick(&f, 5);
    tick(&f, 10);

    /* Normal fill completes, but the OEM ignores its STOP input. Every scan
     * reports running, with other protection healthy and the high-high float clear. */
    f.sample.fill_demand = false;
    unsigned stop_events = 0, last_second_edges = 0, total_edges = 0;
    bool previous = f.panel.heartbeat_high;
    uint32_t first_fault_ms = 0;
    for (unsigned ms = 10; ms <= 10000; ms += 10) {
        struct panel_result out = tick(&f, 10);
        if (out.feedback_fault && !first_fault_ms) first_fault_ms = ms;
        if (out.feedback_fault) assert(!out.heartbeat_high && !out.drive.permit_d && !out.drive.run_cmd);
        if (out.drive.stop_issued) ++stop_events;
        if (out.heartbeat_high != previous) {
            ++total_edges;
            if (ms > 9000) ++last_second_edges;
        }
        previous = out.heartbeat_high;
    }
    printf("Ignored STOP: reported running for 10000 ms, STOP events=%u, "
           "heartbeat edges=%u (final second=%u), IDLE=%d, AUTO authorized=%d.\n",
           stop_events, total_edges, last_second_edges,
           f.panel.outputs.phase == STARTER_IDLE, f.panel.auto_enabled);
    /* The request was first processed at +10 ms. */
    assert(first_fault_ms == 10 + f.panel.outputs.config.confirm_stop_ms);
    if (last_second_edges != 0 || f.panel.auto_enabled || !first_fault_ms) return true;
    f.sample.gpio_b &= (uint8_t)~B_SET_N;
    tick(&f, 1);
    assert(tick(&f, 5).feedback_fault);  /* Motor still running, guard still up. */
    f.sample.motor_stopped = true;
    f.sample.gpio_b &= (uint8_t)~B_GUARD_OK;
    assert(tick(&f, 5).feedback_fault);  /* Recovery with SET held cannot acknowledge. */
    f.sample.gpio_b |= B_SET_N;
    tick(&f, 1); tick(&f, 5);
    f.sample.gpio_b &= (uint8_t)~B_SET_N;
    tick(&f, 1);
    struct panel_result ack = tick(&f, 5);
    assert(!ack.feedback_fault && !ack.auto_enabled && !ack.drive.arm_issued && !ack.heartbeat_high);
    puts("STOP timeout latched; held SET rejected; deliberate acknowledgement required guard open and stopped feedback.");
    return false;
}

static bool start_after_feedback_changes(void)
{
    struct fixture f = {0};
    setup(&f, STARTER_OPEN_STOP);
    arm_from_front_panel(&f);
    struct panel_result permit = tick(&f, 1);
    assert(permit.drive.permit_d && !permit.drive.run_cmd);
    /* Another path picks up the starter after permission closes. The next valid
     * sample reports motor already running as the contact settling time expires. */
    f.sample.motor_stopped = false;
    struct panel_result next = tick(&f, 5);
    printf("OPEN_STOP: stopped feedback went false before START, "
           "START event=%d, START output=%d.\n", next.drive.start_issued, next.drive.run_cmd);
    return next.drive.start_issued || next.drive.run_cmd || next.drive.permit_d ||
           !next.feedback_fault || next.heartbeat_high;
}

int main(void)
{
    bool failed_to_stop = ignored_stop();
    bool started_after_feedback_changed = start_after_feedback_changes();
    return failed_to_stop || started_after_feedback_changed;
}
