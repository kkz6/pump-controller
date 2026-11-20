#include "panel_controls.h"
#include <assert.h>
#include <limits.h>

/* Physical MCP23017 bits, as wired on the released panel and dual main PCB. */
enum { B_START_N=1, B_SET_N=2, B_STOP_OK=4, B_MODE=8, B_NEXT=16, B_GUARD_OK=32, B_MAN_N=64 };
enum { A_AUTO_N=1, A_LOCAL_N=4, A_HOST_N=8 };

struct fixture {
    struct panel_controls p;
    struct panel_sample in;
    uint32_t t;
};

static struct panel_result step(struct fixture *f, uint32_t delta)
{
    f->t += delta;
    f->in.sampled_at_ms = f->t;
    f->in.tank_scanned_at_ms = f->in.protection_checked_at_ms = f->t;
    return panel_controls_step(&f->p, f->t, f->in);
}

static void qualify_monitor(struct fixture *f)
{
    for (unsigned elapsed = 0; elapsed < GUARD_QUIET_MS + 20; elapsed += 10) step(f, 10);
    assert(f->p.guard_recovered);
}

static struct fixture init(enum starter_profile profile, bool key, uint32_t t)
{
    struct fixture f = {.t=t};
    struct starter_config config = {.profile=profile, .harness_profile=profile, .start_range={5,100}, .stop_range={5,100}, .confirm_stop_ms=150, .max_run_ms=60000,
        .contact_settle_ms=5,
        .start_pulse_ms=10, .stop_pulse_ms=10, .independent_shutdown=true};
    assert(panel_controls_configure(&f.p, config, key, 4, 20));
    f.in = (struct panel_sample){.gpio_a=A_LOCAL_N|A_AUTO_N,
                                .gpio_b=B_START_N|B_SET_N|B_STOP_OK|B_GUARD_OK|B_MAN_N,
                                .valid=true,.process_healthy=true, .tank_levels_valid=true,.motor_stopped=true};
    if (key) f.in.gpio_b &= ~B_MAN_N;
    step(&f, 0);
    step(&f, 5);
    if (profile == STARTER_PULSE_STOP) { step(&f, 10); step(&f, 5); }
    qualify_monitor(&f);
    return f;
}

static struct panel_result press_start(struct fixture *f)
{
    f->in.gpio_b &= ~B_START_N;
    assert(!step(f, 1).drive.arm_issued);
    return step(f, 4);
}

static void release_start(struct fixture *f)
{
    f->in.gpio_b |= B_START_N;
    step(f, 1); step(f, 4); step(f, 4);
}

static void test_single_press_and_stop(void)
{
    struct fixture f = init(STARTER_RUN_PAIR, false, UINT32_MAX - 8);
    assert(press_start(&f).drive.arm_issued);
    assert(!panel_controls_step(&f.p, f.t, f.in).drive.start_issued); /* same read */
    struct panel_result r = step(&f, 1);
    assert(r.drive.start_issued && r.drive.permit_d && r.drive.run_cmd);
    f.in.gpio_b &= ~B_STOP_OK;       /* NC opens; no debounce delay for STOP */
    r = step(&f, 1);
    assert(r.drive.stop_issued && !r.drive.permit_d && !r.drive.run_cmd);
    f.in.gpio_b |= B_STOP_OK;
    step(&f, 6);
    assert(!step(&f, 8).drive.arm_issued);  /* START held through stop/release */
    qualify_monitor(&f);
    release_start(&f);
    assert(press_start(&f).drive.arm_issued);
    f.in.gpio_b &= ~B_GUARD_OK;         /* protection trips between ARM and START */
    assert(!step(&f, 1).drive.start_issued);
    f.in.gpio_b |= B_GUARD_OK;
    assert(!step(&f, 7).drive.permit_d);
}

static void test_auto_authorization(void)
{
    struct fixture f = init(STARTER_RUN_PAIR, false, 0);
    f.in.fill_demand = true;
    f.in.gpio_b |= B_MODE;
    step(&f, 1);
    struct panel_result r = step(&f, 4);
    assert(r.mode == PANEL_AUTO && !r.auto_enabled && !r.drive.permit_d);
    f.in.gpio_b &= ~B_MODE;
    step(&f, 1); step(&f, 6);
    qualify_monitor(&f);
    assert(!step(&f, 6).drive.arm_issued);
    assert(press_start(&f).drive.arm_issued);
    assert(step(&f, 1).drive.start_issued);
    release_start(&f);
    f.in.fill_demand = false;
    assert(step(&f, 1).drive.stop_issued);
    step(&f, 6);
    f.in.fill_demand = true;
    assert(step(&f, 1).drive.arm_issued && f.p.auto_enabled);
    assert(step(&f, 1).drive.start_issued);
    f.in.gpio_b &= ~B_STOP_OK;
    r = step(&f, 1);
    assert(r.drive.stop_issued && !r.auto_enabled);
    f.in.gpio_b |= B_STOP_OK;
    step(&f, 10); step(&f, 10);
    qualify_monitor(&f);
    f.in.fill_demand = false; step(&f, 1);
    f.in.fill_demand = true;
    assert(!step(&f, 1).drive.arm_issued);
    assert(press_start(&f).drive.arm_issued);
    f.in.gpio_a = A_AUTO_N|A_HOST_N; /* LOCAL after accepting ARM */
    assert(!step(&f, 1).drive.start_issued && !f.p.auto_enabled);
    f.in.gpio_a = A_AUTO_N|A_LOCAL_N;
    step(&f, 6); step(&f, 6);
    assert(!step(&f, 6).drive.arm_issued);
}

static void test_auto_waits_for_fill(void)
{
    struct fixture f = init(STARTER_RUN_PAIR, false, 0);
    f.in.gpio_b |= B_MODE;
    step(&f, 1); step(&f, 5);
    f.in.gpio_b &= ~B_MODE;
    step(&f, 1); step(&f, 5);
    qualify_monitor(&f);
    struct panel_result r = press_start(&f);
    assert(r.auto_enabled && !r.drive.arm_issued && !r.drive.permit_d);
    release_start(&f);
    f.in.fill_demand = true;
    assert(step(&f, 1).drive.arm_issued);
    assert(step(&f, 1).drive.start_issued);
}

static void test_settings_and_key(void)
{
    struct fixture f = init(STARTER_OPEN_STOP, true, 0);
    f.in.gpio_b |= B_MODE;
    step(&f, 1);
    assert(step(&f, 5).mode == PANEL_MANUAL);
    f.in.gpio_b = (f.in.gpio_b | B_NEXT) & ~B_SET_N;
    step(&f, 1);
    struct panel_result r = step(&f, 5);
    assert(r.set_reset_pressed && r.set_reset_held && r.next_pressed && !r.drive.arm_issued);
    r = step(&f, 1);
    assert(!r.next_pressed && !r.set_reset_pressed && r.set_reset_held);
    assert(!press_start(&f).drive.arm_issued);
    f.in.settings_open = true;
    f.in.gpio_b = (f.in.gpio_b | B_SET_N) & ~B_NEXT;
    release_start(&f);
    assert(!press_start(&f).drive.arm_issued);
    f.in.settings_open = false;
    assert(!step(&f, 5).drive.arm_issued);
    release_start(&f);
    assert(press_start(&f).drive.arm_issued);
    assert(step(&f, 1).drive.permit_d);
    /* Neither key contact selected; drop permission immediately. */
    f.in.gpio_b |= B_MAN_N;
    assert(!step(&f, 1).drive.permit_d);
    f.in.gpio_a &= ~A_AUTO_N;
    step(&f, 1); r = step(&f, 5);
    assert(r.mode == PANEL_AUTO && !r.auto_enabled);
    f.in.gpio_b &= ~B_MAN_N; /* both contacts active is invalid */
    assert(!step(&f, 1).drive.arm_issued);
}

static void test_failed_reads_and_latching_starter(void)
{
    struct fixture f = init(STARTER_PULSE_STOP, false, 0);
    assert(press_start(&f).drive.arm_issued);
    assert(step(&f, 1).drive.permit_d);
    f.in.gpio_b &= ~B_STOP_OK;
    struct panel_result r = step(&f, 1);
    assert(!r.drive.permit_d && !r.drive.run_cmd);
    assert(step(&f, 5).drive.run_cmd);
    assert(!step(&f, 10).drive.run_cmd);
    f.in.valid = false;
    assert(!step(&f, 1).drive.permit_d);
    f.in.valid = true; f.in.gpio_b |= B_STOP_OK;
    assert(!step(&f, 1).drive.permit_d);
    assert(step(&f, 5).drive.stop_issued);  /* synchronization after GPIO failure */
    step(&f, 10); step(&f, 6);
    r = panel_controls_step(&f.p, f.t+21, f.in); /* stale but nominally valid read */
    assert(!r.auto_enabled && !r.drive.arm_issued && !r.drive.permit_d);
}

static void test_external_monitor(void)
{
    struct fixture f = init(STARTER_RUN_PAIR, false, UINT32_MAX - GUARD_QUIET_MS - 180);
    f.in.gpio_b &= ~B_GUARD_OK; /* Guard awaiting the two deliberate cabinet actions. */
    bool old = f.p.heartbeat_high;
    unsigned edges = 0;
    for (unsigned i = 0; i < 40; ++i) {
        struct panel_result out = step(&f, 10);
        edges += old != out.heartbeat_high;
        old = out.heartbeat_high;
        assert(!out.drive.arm_issued && !out.drive.permit_d && !out.drive.run_cmd);
    }
    assert(edges == 4); /* 5 Hz, including across a 32-bit clock wrap. */
    assert(!press_start(&f).drive.arm_issued);
    f.in.gpio_b |= B_GUARD_OK;
    assert(!step(&f, 10).drive.arm_issued); /* Held START cannot start on guard closure. */
    release_start(&f);
    assert(press_start(&f).drive.arm_issued);
    assert(step(&f, 1).drive.start_issued);

    /* Expander still responding but process conversions stuck at one timestamp. */
    const uint32_t stale = f.in.protection_checked_at_ms;
    for (unsigned i = 0; i < 8; ++i) {
        f.t += 10;
        f.in.sampled_at_ms = f.t;
        f.in.protection_checked_at_ms = stale;
        struct panel_result out = panel_controls_step(&f.p, f.t, f.in);
        if (i >= 2) assert(!out.heartbeat_high && !out.drive.permit_d && !out.drive.run_cmd);
    }
    assert(!step(&f, 10).heartbeat_high); /* First fresh conversion follows a gap. */
    for (unsigned i = 0; i < GUARD_QUIET_MS / 10 - 1; ++i)
        assert(!step(&f, 10).heartbeat_high);
    assert(step(&f, 10).heartbeat_high);
    assert(!f.p.auto_enabled && !f.p.pending_start);

    f.in.valid = false;
    assert(!step(&f, 1).heartbeat_high);
    f.in.valid = true;
    for (unsigned i = 0; i < GUARD_QUIET_MS / 10 - 1; ++i)
        assert(!step(&f, 10).heartbeat_high);
    assert(step(&f, 10).heartbeat_high);
    /* Simulate loss of a fresh panel frame with valid process updates. */
    const uint32_t old_panel = f.t;
    for (unsigned i = 0; i < 8; ++i) {
        f.t += 10;
        f.in.sampled_at_ms = old_panel;
        f.in.protection_checked_at_ms = f.t;
        struct panel_result out = panel_controls_step(&f.p, f.t, f.in);
        if (i >= 2) assert(!out.heartbeat_high && !out.drive.permit_d);
    }
}

static void test_restore_with_auto_key_and_held_demand(void)
{
    for (enum starter_profile profile = STARTER_RUN_PAIR; profile <= STARTER_PULSE_STOP; ++profile) {
        struct fixture f = init(profile, true, 0);
        f.in.gpio_b |= B_MAN_N;
        f.in.gpio_a &= ~A_AUTO_N;
        f.in.fill_demand = true;
        step(&f, 1); step(&f, 5);
        qualify_monitor(&f);
        assert(press_start(&f).drive.arm_issued);
        step(&f, 1);
        /* Power disappears with AUTO selected, demand present and START still held. */
        struct starter_config saved_service_config = f.p.outputs.config;
        assert(panel_controls_configure(&f.p, saved_service_config, true, 4, 20));
        f.in.gpio_b &= ~B_GUARD_OK;
        for (unsigned i = 0; i < GUARD_QUIET_MS / 10 + 10; ++i) {
            struct panel_result out = step(&f, 10);
            assert(!out.auto_enabled && !out.drive.arm_issued && !out.drive.start_issued);
        }
        assert(f.p.mode == PANEL_AUTO && f.p.guard_recovered);
        f.in.gpio_b |= B_GUARD_OK; /* External reset/enable occurred. */
        for (unsigned i = 0; i < 15; ++i) {
            struct panel_result out = step(&f, 10);
            assert(!out.auto_enabled && !out.drive.arm_issued && !out.drive.start_issued);
        }
        release_start(&f);
        assert(press_start(&f).drive.arm_issued);
        assert(step(&f, 1).drive.permit_d);
    }
}

static void authorize_fill(struct fixture *f, bool automatic)
{
    if (automatic) {
        f->in.gpio_b |= B_MODE;
        step(f, 1); step(f, 4);
        f->in.gpio_b &= ~B_MODE;
        step(f, 1); step(f, 5);
        qualify_monitor(f);
        f->in.fill_demand = true;
    }
    assert(press_start(f).drive.arm_issued);
    /* OPEN_STOP begins with the A permission, then issues START after settling. */
    assert(step(f, 1).drive.permit_d);
}

static void expect_stop(struct fixture *f, enum starter_profile profile, struct panel_result r)
{
    assert(!r.drive.permit_d && !r.drive.start_issued && !r.drive.run_cmd);
    if (profile == STARTER_PULSE_STOP) {
        assert(!r.drive.stop_issued);
        r = step(f, 5);
        assert(r.drive.stop_issued && r.drive.run_cmd && !r.drive.permit_d);
        assert(!step(f, 10).drive.run_cmd);
    } else {
        assert(r.drive.stop_issued);
    }
    f->in.motor_stopped = true;
    step(f, 5);
    assert(f->p.outputs.phase == STARTER_IDLE);
}

static void test_full_and_timeout(enum starter_profile profile, bool automatic)
{
    struct fixture f = init(profile, false, 0);
    authorize_fill(&f, automatic);
    /* Full arrives during the earliest active phase and overrides held START
     * and a contradictory automatic demand. */
    f.in.tank_wet_mask = 15;
    struct panel_result r = step(&f, 1);
    assert(!r.run_timed_out);
    expect_stop(&f, profile, r);
    release_start(&f);
    assert(!press_start(&f).drive.arm_issued);
    f.in.tank_wet_mask = 7;
    assert(!step(&f, 1).drive.arm_issued); /* Same demand and held START. */
    release_start(&f);
    if (automatic) {
        f.in.fill_demand = false;
        step(&f, 1);
        f.in.fill_demand = true;
        assert(!step(&f, 1).drive.arm_issued); /* L1–L3 still wet despite a new demand. */
        f.in.tank_wet_mask = 0;
        assert(step(&f, 1).drive.arm_issued); /* Only a genuinely low tank can start. */
    } else {
        assert(press_start(&f).drive.arm_issued);
    }
    assert(step(&f, 1).drive.permit_d);

    /* New run and clock wrap: keep the highest probe dry indefinitely. */
    f = init(profile, false, UINT32_MAX - (automatic ? 6090u : 3060u));
    f.p.outputs.config.max_run_ms = 32;
    authorize_fill(&f, automatic);
    uint32_t accepted = f.t;
    step(&f, 5);
    f.in.motor_stopped = false;
    step(&f, 10); step(&f, 10);
    assert(!step(&f, 6).run_timed_out);
    assert(f.t - accepted == 31);
    r = step(&f, 1);
    assert(f.t < accepted); /* The configured deadline crossed UINT32_MAX. */
    assert(r.run_timed_out && !r.auto_enabled);
    expect_stop(&f, profile, r);
    f.in.fill_demand = false; step(&f, 1);
    f.in.fill_demand = true;
    release_start(&f);
    assert(!press_start(&f).drive.arm_issued && f.p.run_timed_out);
    release_start(&f);
    f.in.gpio_b &= ~B_SET_N;
    step(&f, 1);
    r = step(&f, 4);
    assert(!r.run_timed_out && !r.drive.arm_issued && !r.auto_enabled);
    f.in.gpio_b |= B_SET_N;
    step(&f, 1); step(&f, 5);
    assert(press_start(&f).drive.arm_issued);
}

static void test_level_input_and_commissioning(void)
{
    struct fixture f = init(STARTER_RUN_PAIR, false, 0);
    struct starter_config cfg = f.p.outputs.config;
    cfg.max_run_ms = 0;
    assert(!panel_controls_configure(&f.p, cfg, false, 4, 20));
    cfg.max_run_ms = UINT32_MAX;
    assert(!panel_controls_configure(&f.p, cfg, false, 4, 20));
    f = init(STARTER_RUN_PAIR, false, 0);
    assert(press_start(&f).drive.arm_issued);
    f.in.tank_wet_mask = 15;
    assert(!step(&f, 1).drive.start_issued && !f.p.pending_start); /* Full between ARM and START. */
    f.in.tank_wet_mask = 0;
    release_start(&f);
    assert(press_start(&f).drive.arm_issued);
    assert(step(&f, 1).drive.start_issued);
    f.in.tank_wet_mask = 8; /* L4 wet but lower probes dry: bad ordering or cable fault. */
    assert(step(&f, 1).drive.stop_issued && !f.p.guard_recovered);
    for (uint8_t mask = 0; mask < 16; ++mask) {
        f = init(STARTER_RUN_PAIR, false, 0);
        f.in.tank_wet_mask = mask;
        step(&f, 1);
        assert(f.p.guard_recovered == (mask == 0 || mask == 1 || mask == 3 || mask == 7 || mask == 15));
    }
    f.in.tank_levels_valid = false; /* Missing acquisition does not mean an empty tank. */
    assert(!step(&f, 1).heartbeat_high && !f.p.guard_recovered);
}

static void test_auto_at_full_and_loss_of_low_before_start(void)
{
    struct fixture f = init(STARTER_RUN_PAIR, false, 0);
    f.in.tank_wet_mask = 15;
    f.in.gpio_b |= B_MODE;
    step(&f, 1); step(&f, 4);
    f.in.gpio_b &= ~B_MODE;
    step(&f, 1); step(&f, 5);
    qualify_monitor(&f);
    struct panel_result r = press_start(&f);
    assert(r.auto_enabled && !r.drive.arm_issued && !r.drive.permit_d && !r.drive.run_cmd);
    release_start(&f);
    f.in.tank_wet_mask = 7;
    f.in.fill_demand = true;
    assert(!step(&f, 1).drive.arm_issued);
    f.in.tank_wet_mask = 0;
    assert(step(&f, 1).drive.arm_issued);
    f.in.tank_wet_mask = 1;
    r = step(&f, 1);
    assert(r.drive.stop_issued && !r.drive.start_issued && !r.drive.permit_d);
    f.in.fill_demand = false; step(&f, 6);
    f.in.fill_demand = true; f.in.tank_wet_mask = 0;
    assert(step(&f, 1).drive.arm_issued);
    assert(step(&f, 1).drive.start_issued);
    for (uint8_t mask = 1; mask < 15; mask = 2 * mask + 1) {
        f.in.tank_wet_mask = mask;
        assert(step(&f, 1).drive.permit_d); /* Rising intermediate levels are normal in a fill. */
    }
}

static void test_independent_scan_age(void)
{
    struct fixture f = init(STARTER_RUN_PAIR, false, UINT32_MAX - 3100u);
    authorize_fill(&f, false);
    uint32_t scan = f.in.tank_scanned_at_ms;
    for (unsigned age = 10; age <= TANK_MAX_SCAN_AGE_MS; age += 10) {
        f.t += 10;
        f.in.protection_checked_at_ms = f.in.sampled_at_ms = f.t;
        assert(f.in.tank_scanned_at_ms == scan);
        assert(panel_controls_step(&f.p, f.t, f.in).drive.permit_d);
    }
    f.t++;
    f.in.protection_checked_at_ms = f.in.sampled_at_ms = f.t;
    struct panel_result r = panel_controls_step(&f.p, f.t, f.in);
    assert(r.drive.stop_issued && !r.drive.permit_d && !r.heartbeat_high);
    /* Keep the same expired acquisition while both unrelated heartbeats advance. */
    f.in.gpio_b |= B_START_N;
    for (unsigned i = 0; i < 10; ++i) {
        if (i == 5) f.in.gpio_b &= ~B_START_N;
        f.t++;
        f.in.protection_checked_at_ms = f.in.sampled_at_ms = f.t;
        r = panel_controls_step(&f.p, f.t, f.in);
        assert(!r.drive.arm_issued && !r.drive.start_issued && !r.drive.permit_d && !r.heartbeat_high);
    }
    release_start(&f);
    assert(!press_start(&f).drive.arm_issued);
    f = init(STARTER_RUN_PAIR, false, 0);
    f.in.tank_scanned_at_ms--; /* Young but older than the latest completed scan. */
    r = panel_controls_step(&f.p, f.t, f.in);
    assert(!r.heartbeat_high && !f.p.guard_recovered);
    qualify_monitor(&f);
    f.in.tank_scanned_at_ms = f.t + 1;
    assert(!panel_controls_step(&f.p, f.t, f.in).heartbeat_high);
}

static void test_timeout_rejects_set_begun_before_trip(void)
{
    struct fixture f = init(STARTER_RUN_PAIR, false, 0);
    f.p.outputs.config.max_run_ms = 20;
    authorize_fill(&f, false);
    release_start(&f); /* Run age 9 ms; test a press whose debounce ends after confirmed stop. */
    f.p.debounce_ms = 20;
    f.in.gpio_b &= ~B_SET_N;
    step(&f, 10);
    assert(step(&f, 1).run_timed_out);
    step(&f, 5);
    assert(f.p.outputs.phase == STARTER_IDLE);
    struct panel_result r = step(&f, 14);
    assert(r.set_reset_pressed && r.run_timed_out);
    f.in.gpio_b |= B_SET_N;
    step(&f, 1); step(&f, 20); step(&f, 20);
    f.in.gpio_b &= ~B_SET_N;
    step(&f, 1); r = step(&f, 20);
    assert(r.set_reset_pressed && !r.run_timed_out && !r.auto_enabled && !r.drive.arm_issued);
}

int main(void)
{
    test_auto_at_full_and_loss_of_low_before_start();
    test_independent_scan_age();
    test_timeout_rejects_set_begun_before_trip();
    test_level_input_and_commissioning();
    for (enum starter_profile profile = STARTER_RUN_PAIR; profile <= STARTER_PULSE_STOP; ++profile) {
        test_full_and_timeout(profile, false);
        test_full_and_timeout(profile, true);
    }
    test_restore_with_auto_key_and_held_demand();
    test_external_monitor();
    test_single_press_and_stop();
    test_auto_authorization();
    test_auto_waits_for_fill();
    struct fixture fault = init(STARTER_RUN_PAIR, false, 0);
    fault.in.process_healthy = false;
    fault.in.gpio_a = A_HOST_N | A_AUTO_N; /* transfer LOCAL */
    fault.in.gpio_b = (fault.in.gpio_b | B_NEXT) & ~B_SET_N;
    step(&fault, 1);
    struct panel_result ui = step(&fault, 5);
    assert(ui.set_reset_pressed && ui.next_pressed && !ui.drive.arm_issued && !ui.drive.permit_d);
    fault.in.process_healthy = true;
    fault.in.gpio_a = A_LOCAL_N | A_AUTO_N;
    assert(!step(&fault, 5).drive.start_issued && !fault.p.auto_enabled);
    test_settings_and_key();
    test_failed_reads_and_latching_starter();
    struct fixture f = init(STARTER_RUN_PAIR, false, 0);
    assert(press_start(&f).drive.arm_issued);
    assert(!step(&f, 25).drive.start_issued);  /* no ticks since ARM */
    assert(!step(&f, 5).drive.permit_d);
    f.in.gpio_a |= A_HOST_N;  /* both transfer inputs inactive */
    release_start(&f);
    assert(!press_start(&f).drive.arm_issued);
}
