/* Offline diagnostic for the direct, two-relay board. No target GPIO or motor is touched.
 * The control decisions come from the repository C sources. The external contacts below
 * implement the three-wire circuit in docs/connections.md or an electronic latch.
 * A return of 1 reports a violated behavior; 2 means the setup could not be established.
 */
#include "panel_controls.h"
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

enum { PANEL_START_N = 1, PANEL_SET_N = 2, PANEL_STOP_OK = 4, PANEL_SUPPLY_OK = 32,
       KEY_MAN_N = 64, KEY_AUTO_N = 1 };

struct rig {
    struct panel_controls controls;
    struct panel_sample input;
    struct panel_result result;
    uint32_t now;
    bool contactor, stop_closed, overload_closed, k2_welded;
    bool electronic, swapped;
};

static void require_setup(bool condition, const char *message)
{
    if (!condition) {
        fprintf(stderr, "Invalid test setup: %s\n", message);
        exit(2);
    }
}

static void apply_external_contacts(struct rig *r)
{
    if (r->electronic) {
        /* OEM electronics on a separate healthy supply. STOP takes priority. */
        bool stop = r->swapped ? r->result.drive.permit_d : r->result.drive.run_cmd;
        bool start = r->swapped ? r->result.drive.run_cmd : r->result.drive.permit_d;
        if (stop) r->contactor = false;
        else if (start) r->contactor = true;
        return;
    }
    /* K1 in series with all three-wire pickup/holding branches. K2 is across START.
     * The original green button remains released throughout these experiments.
     * The auxiliary holding contact follows the contactor. */
    r->contactor = r->stop_closed && r->overload_closed && r->result.drive.permit_d &&
                   (r->contactor || r->result.drive.run_cmd || r->k2_welded);
}

static void sample(struct rig *r, unsigned delta_ms)
{
    r->now += delta_ms;
    r->input.sampled_at_ms = r->now;
    r->input.protection_checked_at_ms = r->now;
    r->input.tank_scanned_at_ms = r->now;
    r->input.voltage.acquired_ms = r->now;
    /* Prompt, correct stopped feedback on every control cycle is favorable to the controller. */
    r->input.motor_stopped = !r->contactor;
    r->result = panel_controls_step(&r->controls, r->now, r->input);
    apply_external_contacts(r);
}

static void advance(struct rig *r, unsigned elapsed_ms)
{
    while (elapsed_ms > 0) {
        unsigned step_ms = elapsed_ms > 10 ? 10 : elapsed_ms;
        sample(r, step_ms);
        elapsed_ms -= step_ms;
    }
}

static struct rig powered_board(enum starter_profile profile, uint32_t pickup_ms)
{
    struct rig r = {.stop_closed = true, .overload_closed = true,
                    .electronic = profile == STARTER_PULSE_STOP};
    const struct starter_config config = {
        .profile = profile, .harness_profile = profile, .independent_shutdown = true,
        .contact_settle_ms = 5, .start_pulse_ms = pickup_ms, .stop_pulse_ms = 10,
        .start_range = {5, 500}, .stop_range = {5, 100},
        .confirm_stop_ms = 600, .max_run_ms = 60000
    };
    /* independent_shutdown is the API's required configuration input. It does not
     * add a cabinet component to either external-circuit model. */
    const struct voltage_limits voltage = {200000, 250000, 5000, 20, 230000, 5750000};
    require_setup(direct_starter_configure(&r.controls, config, false, 4, 20, voltage),
                  "direct board configuration rejected");
    r.input = (struct panel_sample){
        .gpio_a = KEY_AUTO_N,
        .gpio_b = PANEL_START_N | PANEL_SET_N | PANEL_STOP_OK | PANEL_SUPPLY_OK | KEY_MAN_N,
        .valid = true, .process_healthy = true, .tank_levels_valid = true,
        .voltage = {.valid = true, .counts = 5750000}
    };
    return r;
}

static struct rig start_pump(enum starter_profile profile, uint32_t pickup_ms)
{
    struct rig r = powered_board(profile, pickup_ms);
    advance(&r, 3200);
    r.input.gpio_b &= ~PANEL_START_N;
    sample(&r, 1);
    sample(&r, 4);
    require_setup(r.result.drive.arm_issued, "fresh panel START did not arm the board");
    sample(&r, 5);
    if (!r.electronic) sample(&r, 5);
    require_setup(r.result.drive.start_issued && r.contactor, "contactor failed to pick up");
    r.input.gpio_b |= PANEL_START_N;
    return r;
}

static unsigned original_interruption(bool welded, bool overload)
{
    struct rig r = start_pump(STARTER_OPEN_STOP, 10);
    r.k2_welded = welded;
    advance(&r, 40);
    require_setup(r.contactor && r.result.drive.permit_d && !r.result.drive.run_cmd,
                  "expected a sealed run with pickup command inactive");
    if (overload) r.overload_closed = false; else r.stop_closed = false;
    apply_external_contacts(&r);
    require_setup(!r.contactor, "original STOP/overload did not interrupt the coil");
    advance(&r, 1000);
    if (overload) r.overload_closed = true; else r.stop_closed = true;
    apply_external_contacts(&r);
    printf("K2 %s; %s; A command=%d, B command=%d; contactor after restoration=%s\n",
           welded ? "welded" : "healthy", overload ? "overload reset" : "original STOP released",
           r.result.drive.permit_d, r.result.drive.run_cmd, r.contactor ? "ON" : "OFF");
    return r.contactor;
}

static unsigned stop_during_pickup(void)
{
    struct rig r = start_pump(STARTER_OPEN_STOP, 500);
    advance(&r, 50);
    r.stop_closed = false;
    apply_external_contacts(&r);
    require_setup(!r.contactor, "original STOP did not release the contactor");
    advance(&r, 250);
    r.stop_closed = true;
    apply_external_contacts(&r);
    printf("No welds; 250 ms original STOP during 500 ms pickup; A command=%d, B command=%d; "
           "contactor on release=%s\n", r.result.drive.permit_d, r.result.drive.run_cmd,
           r.contactor ? "ON" : "OFF");
    return r.contactor;
}

static unsigned electronic_bus_loss(void)
{
    struct rig r = start_pump(STARTER_PULSE_STOP, 10);
    advance(&r, 40);
    require_setup(r.contactor && !r.result.drive.permit_d && !r.result.drive.run_cmd,
                  "electronic starter did not remain latched after START pulse");
    r.input.valid = false;
    unsigned stop_samples = 0;
    for (unsigned i = 0; i < 700; ++i) {
        sample(&r, 10);
        if (r.result.drive.run_cmd) ++stop_samples;
    }
    printf("Electronic starter; 7 s continuous panel bus loss; K2 STOP samples=%u; "
           "heartbeat=%d; OEM latch=%s\n", stop_samples, r.result.heartbeat_high,
           r.contactor ? "ON" : "OFF");
    return r.contactor;
}

static unsigned electronic_powerup(bool swapped)
{
    struct rig r = powered_board(STARTER_PULSE_STOP, 10);
    r.swapped = swapped;
    unsigned first_k2_ms = 0, arm_events = 0;
    for (unsigned i = 0; i < 100; ++i) {
        sample(&r, 1);
        if (r.result.drive.run_cmd && !first_k2_ms) first_k2_ms = r.now;
        if (r.result.drive.arm_issued) ++arm_events;
    }
    require_setup(first_k2_ms && !arm_events, "expected the unauthorised-start test to observe a boot STOP pulse without an ARM");
    printf("Electronic starter; %s J30/J35 at power-up; first K2 high at %u ms; "
           "ARM events=%u; OEM latch=%s\n", swapped ? "interchanged" : "correct",
           first_k2_ms, arm_events, r.contactor ? "ON" : "OFF");
    return r.contactor;
}

int main(void)
{
    puts("Offline contact model. ON after release, loss or power-up is an unmet requirement.");
    unsigned violations = original_interruption(false, false);
    violations += original_interruption(true, false);
    violations += original_interruption(true, true);
    violations += stop_during_pickup();
    violations += electronic_bus_loss();
    violations += electronic_powerup(false);
    violations += electronic_powerup(true);
    printf("Cases ending ON: %u. No physical starter has been tested.\n", violations);
    return violations ? 1 : 0;
}
