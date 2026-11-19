#include "starter_outputs.h"
#include "command_leds.h"
#include <assert.h>

static struct starter_drive check(struct starter_outputs *s, uint32_t now, bool healthy,
                                  bool stopped, enum starter_command cmd, bool a, bool b)
{
    struct starter_drive d = starter_step(s, now, TRANSFER_HOST, healthy, stopped, cmd);
    assert(d.permit_d == a && d.run_cmd == b);
    return d;
}

/* Test fixture timings, independent of the values required by any real starter. */
static struct starter_config config(enum starter_profile profile)
{
    return (struct starter_config){.profile = profile, .harness_profile = profile, .start_range={5,100}, .stop_range={5,100}, .confirm_stop_ms=150,
        .contact_settle_ms = 20,
        .start_pulse_ms = 60, .stop_pulse_ms = 40, .independent_shutdown = true};
}

static void test_maintained(void)
{
    struct starter_outputs s;
    assert(starter_configure(&s, config(STARTER_RUN_PAIR)));
    check(&s, 0, true, true, STARTER_START, false, false); /* stale at power up */
    check(&s, 20, true, true, STARTER_NONE, false, false);
    check(&s, 21, true, true, STARTER_START, false, false); /* disarmed */
    assert(check(&s, 22, true, true, STARTER_ARM, false, false).arm_issued);
    assert(!check(&s, 23, true, true, STARTER_ARM, false, false).arm_issued);
    assert(check(&s, 25, true, true, STARTER_START, true, true).start_issued);
    check(&s, 5000, true, false, STARTER_NONE, true, true);
    assert(check(&s, 5001, false, false, STARTER_NONE, false, false).stop_issued);
    check(&s, 5100, true, true, STARTER_NONE, false, false);
    check(&s, 5101, true, true, STARTER_START, false, false);
}

static void test_open_stop(void)
{
    struct starter_outputs s;
    assert(starter_configure(&s, config(STARTER_OPEN_STOP)));
    check(&s, 0, true, true, STARTER_NONE, false, false);
    check(&s, 20, true, true, STARTER_NONE, false, false);
    check(&s, 21, true, true, STARTER_ARM, false, false);
    assert(!check(&s, 22, true, true, STARTER_START, true, false).start_issued);
    assert(check(&s, 42, true, true, STARTER_NONE, true, true).start_issued);
    check(&s, 101, true, false, STARTER_NONE, true, true);
    check(&s, 102, true, false, STARTER_NONE, true, false);
    assert(check(&s, 104, true, false, STARTER_STOP, false, false).stop_issued);
}

static void test_pulse_stop(void)
{
    struct starter_outputs s;
    struct pump_command_leds leds = {0};
    uint8_t olat[] = {0x03, 0x14};
    assert(starter_configure(&s, config(STARTER_PULSE_STOP)));
    check(&s, 0, false, false, STARTER_NONE, false, false);
    assert(check(&s, 20, false, false, STARTER_NONE, false, true).stop_issued);
    check(&s, 60, true, true, STARTER_NONE, false, false);
    check(&s, 80, true, true, STARTER_NONE, false, false);
    check(&s, 81, true, false, STARTER_ARM, false, false); /* feedback not stopped */
    check(&s, 82, true, true, STARTER_START, false, false);
    check(&s, 83, true, true, STARTER_ARM, false, false);
    struct starter_drive d = check(&s, 84, true, true, STARTER_START, true, false);
    pump_command_leds_record(&leds, 84, d.start_issued, d.stop_issued);
    pump_command_leds_render(&leds, 84, olat);
    assert(olat[0] == 0x03 && olat[1] == 0x94);
    check(&s, 100, false, false, STARTER_STOP, false, false);
    check(&s, 119, false, false, STARTER_STOP, false, false);
    d = check(&s, 120, false, false, STARTER_STOP, false, true);
    pump_command_leds_record(&leds, 120, d.start_issued, d.stop_issued);
    pump_command_leds_render(&leds, 120, olat);
    assert(olat[0] == 0x83 && olat[1] == 0x14);
    check(&s, 160, false, false, STARTER_STOP, false, false); /* held STOP does not extend pulse */
    check(&s, 180, true, true, STARTER_STOP, false, false);
    check(&s, 181, true, true, STARTER_START, false, false); /* no repeat after fault */
    check(&s, 182, true, true, STARTER_ARM, false, false);
    check(&s, 183, true, true, STARTER_START, true, false);
    check(&s, 243, true, false, STARTER_NONE, false, false); /* OEM latches own motor */
    struct starter_drive local = starter_step(&s, 244, TRANSFER_LOCAL, true, true, STARTER_ARM);
    assert(!local.arm_issued && !local.permit_d && !local.run_cmd && !s.armed);
    local = starter_step(&s, 245, TRANSFER_UNKNOWN, true, true, STARTER_START);
    assert(!local.permit_d && !local.run_cmd);
    check(&s, 246, true, true, STARTER_START, false, false); /* return with held START */
    assert(check(&s, 266, true, false, STARTER_START, false, true).stop_issued);
}

static void test_stop_deadline_and_rollover(void)
{
    struct starter_outputs s;
    struct starter_config cfg = config(STARTER_RUN_PAIR);
    uint32_t start = UINT32_MAX - 50;
    assert(starter_configure(&s, cfg));
    check(&s, start, true, true, STARTER_NONE, false, false);
    check(&s, start + 20, true, true, STARTER_NONE, false, false);
    assert(check(&s, start + 21, true, true, STARTER_ARM, false, false).arm_issued);
    check(&s, start + 22, true, true, STARTER_START, true, true);
    check(&s, start + 23, true, false, STARTER_STOP, false, false);
    check(&s, start + 23 + cfg.confirm_stop_ms - 1, true, false, STARTER_STOP, false, false);
    assert(s.phase == STARTER_SETTLING);
    check(&s, start + 23 + cfg.confirm_stop_ms, true, false, STARTER_STOP, false, false);
    assert(s.phase == STARTER_FEEDBACK_FAULT);
    starter_step(&s, 200, TRANSFER_UNKNOWN, false, false, STARTER_NONE);
    assert(s.phase == STARTER_FEEDBACK_FAULT);
    check(&s, 210, true, true, STARTER_ACKNOWLEDGE, false, false);
    assert(s.phase == STARTER_FEEDBACK_FAULT); /* External permission still up. */
}

int main(void)
{
    struct starter_outputs s;
    for (enum starter_profile profile = STARTER_RUN_PAIR; profile <= STARTER_PULSE_STOP; ++profile) {
        struct starter_config selected = config(profile);
        selected.independent_shutdown = false;
        assert(!starter_configure(&s, selected));
        selected.independent_shutdown = true;
        for (enum starter_profile harness = STARTER_DISABLED; harness <= STARTER_PULSE_STOP; ++harness) {
            selected.harness_profile = harness;
            assert(starter_configure(&s, selected) == (profile == harness));
        }
    }
    struct starter_config bad = config(STARTER_PULSE_STOP);
    bad.independent_shutdown = false;
    assert(!starter_configure(&s, bad));
    check(&s, 0, true, true, STARTER_START, false, false);
    bad = config(STARTER_OPEN_STOP);
    bad.start_pulse_ms = 0;
    assert(!starter_configure(&s, bad));
    assert(starter_transfer_decode(true, true) == TRANSFER_UNKNOWN);
    assert(starter_transfer_decode(false, false) == TRANSFER_UNKNOWN);
    assert(starter_transfer_decode(false, true) == TRANSFER_HOST);
    assert(starter_transfer_decode(true, false) == TRANSFER_LOCAL);
    test_maintained();
    test_open_stop();
    test_pulse_stop();
    test_stop_deadline_and_rollover();
    bad = config(STARTER_PULSE_STOP);
    bad.stop_pulse_ms = bad.stop_range.max_ms + 1;
    assert(!starter_configure(&s, bad));
    bad = config(STARTER_PULSE_STOP);
    bad.start_pulse_ms = bad.start_range.min_ms - 1;
    assert(!starter_configure(&s, bad));
    bad = config(STARTER_PULSE_STOP);
    bad.start_range.max_ms = INT32_MAX;
    assert(!starter_configure(&s, bad));
    bad = config(STARTER_PULSE_STOP);
    bad.confirm_stop_ms = 2 * bad.contact_settle_ms + bad.stop_pulse_ms;
    assert(!starter_configure(&s, bad));
    assert(starter_configure(&s, config(STARTER_PULSE_STOP)));
    check(&s, UINT32_MAX-9, true, true, STARTER_NONE, false, false);
    assert(check(&s, 10, true, true, STARTER_NONE, false, true).stop_issued);
    return 0;
}
