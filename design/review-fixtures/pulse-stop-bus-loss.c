/* Exercise the production sequencer with simulated readings. No GPIO or motor hardware. */
#include "panel_controls.h"
#include <assert.h>
#include <stdio.h>

enum { START_N = 1, SET_N = 2, STOP_OK = 4, HIGH_HIGH_OK = 32, KEY_MAN_N = 64 };
enum { KEY_AUTO_N = 1, LOCAL_N = 4 };

static struct panel_result sample(struct panel_controls *panel, struct panel_sample *input,
                                  uint32_t timestamp)
{
    input->sampled_at_ms = timestamp;
    return panel_controls_step(panel, timestamp, *input);
}

int main(void)
{
    struct panel_controls panel;
    struct starter_config config = {.profile = STARTER_PULSE_STOP, .contact_settle_ms = 5,
        .start_pulse_ms = 10, .stop_pulse_ms = 10, .independent_shutdown = true};
    struct panel_sample input = {
        .gpio_a = KEY_AUTO_N | LOCAL_N, /* HOST is asserted low. */
        .gpio_b = START_N | SET_N | STOP_OK | HIGH_HIGH_OK | KEY_MAN_N,
        .valid = true, .process_healthy = true, .motor_stopped = true};
    assert(panel_controls_configure(&panel, config, false, 4, 20));
    sample(&panel, &input, 0);
    assert(sample(&panel, &input, 5).drive.stop_issued); /* Synchronization pulse. */
    sample(&panel, &input, 15);
    sample(&panel, &input, 20);
    input.gpio_b &= ~START_N;
    sample(&panel, &input, 21);
    assert(sample(&panel, &input, 25).drive.arm_issued);
    assert(sample(&panel, &input, 26).drive.start_issued);
    input.motor_stopped = false;
    input.gpio_b |= START_N;
    sample(&panel, &input, 36); /* OEM starter has latched the preceding pulse. */

    struct panel_controls control = panel;
    struct panel_sample readable = input;
    readable.gpio_b &= ~STOP_OK;
    sample(&control, &readable, 37);
    struct panel_result control_stop = sample(&control, &readable, 42);
    assert(control_stop.drive.stop_issued && control_stop.drive.run_cmd);
    puts("Positive control: pressing STOP with a readable panel commands K2.");

    input.valid = false; /* Repeated failed reads, while the control task keeps running. */
    unsigned stop_events = 0, stop_drive_samples = 0;
    for (unsigned i = 1; i <= 120; i++) {
        struct panel_result result = sample(&panel, &input, 36 + 50 * i);
        stop_events += result.drive.stop_issued;
        stop_drive_samples += result.drive.run_cmd; /* K2 is STOP in this profile. */
    }
    printf("After START, 120 invalid reads over 6 s: %u STOP events, %u K2 drive samples\n",
           stop_events, stop_drive_samples);
    return 0;
}
