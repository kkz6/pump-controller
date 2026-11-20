/* Exercise the actual panel sequencer; model only the external missing-edge deadline. */
#include "panel_controls.h"
#include <assert.h>
#include <stdio.h>

enum { START_N=1, SET_N=2, STOP_OK=4, GUARD_OK=32, MAN_N=64, AUTO_N=1, LOCAL_N=4 };
enum { MONITOR_LIMIT_MS=1000 }; /* Maximum permitted receiver dropout. Bench measurement required. */

static struct panel_result sample(struct panel_controls *p, struct panel_sample *in, uint32_t t)
{
    in->tank_scanned_at_ms = in->protection_checked_at_ms = in->sampled_at_ms = t;
    return panel_controls_step(p, t, *in);
}

int main(void)
{
    struct panel_controls p;
    struct starter_config cfg = {.profile=STARTER_PULSE_STOP, .harness_profile=STARTER_PULSE_STOP,
        .start_range={5,100}, .stop_range={5,100}, .confirm_stop_ms=150, .max_run_ms=60000,
        .contact_settle_ms=5, .start_pulse_ms=10, .stop_pulse_ms=10, .independent_shutdown=true};
    struct panel_sample in = {.gpio_a=AUTO_N|LOCAL_N, .gpio_b=START_N|SET_N|STOP_OK|MAN_N,
        .valid=true, .process_healthy=true, .tank_levels_valid=true, .motor_stopped=true};
    assert(panel_controls_configure(&p, cfg, false, 4, 20));
    bool previous = false;
    uint32_t last_rise = 0;
    for (uint32_t t=0; t<=3600; t+=10) {
        struct panel_result r = sample(&p, &in, t);
        if (r.heartbeat_high && !previous) last_rise = t;
        assert(!r.drive.arm_issued && !r.drive.start_issued);
        previous = r.heartbeat_high;
    }
    assert(last_rise == 3600);
    in.gpio_b |= GUARD_OK; /* Simulated monitored reset and separate enable. */
    sample(&p, &in, 3605); sample(&p, &in, 3610);
    in.gpio_b &= ~START_N;
    sample(&p, &in, 3611);
    assert(sample(&p, &in, 3615).drive.arm_issued);
    assert(sample(&p, &in, 3616).drive.start_issued);
    in.motor_stopped = false; /* Simulated OEM starter latched. */
    in.gpio_b |= START_N;
    sample(&p, &in, 3626);
    in.valid = false;
    unsigned stop_events = 0;
    for (uint32_t t=3636; t<=9636; t+=10) {
        struct panel_result r = sample(&p, &in, t);
        stop_events += r.drive.stop_issued;
        assert(!r.heartbeat_high && !r.drive.run_cmd && !r.drive.start_issued);
        if (t-last_rise >= MONITOR_LIMIT_MS) in.gpio_b &= ~GUARD_OK;
    }
    assert(!stop_events && !(in.gpio_b & GUARD_OK));
    in.valid = in.motor_stopped = true;
    for (uint32_t t=9646; t<14000; t+=10) {
        struct panel_result r = sample(&p, &in, t);
        assert(!r.drive.arm_issued && !r.drive.start_issued && !r.auto_enabled);
    }
    puts("Latched START followed by bus failure: no K2 pulse, heartbeat stopped. "
         "Simulated external guard expired; healthy data alone could not restart.");
}
