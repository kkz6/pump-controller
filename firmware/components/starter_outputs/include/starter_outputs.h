#ifndef PUMP_STARTER_OUTPUTS_H
#define PUMP_STARTER_OUTPUTS_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

enum starter_profile { STARTER_DISABLED, STARTER_RUN_PAIR, STARTER_OPEN_STOP, STARTER_PULSE_STOP };
enum starter_command { STARTER_NONE, STARTER_ARM, STARTER_START, STARTER_STOP, STARTER_ACKNOWLEDGE };
enum starter_transfer { TRANSFER_UNKNOWN, TRANSFER_HOST, TRANSFER_LOCAL };
enum starter_phase { STARTER_IDLE, STARTER_PERMISSION, STARTER_STARTING, STARTER_RUNNING,
                     STARTER_RELEASING, STARTER_STOPPING, STARTER_SETTLING, STARTER_FEEDBACK_FAULT };

struct starter_pulse_range {
    uint32_t min_ms, max_ms; /* Limits recorded when the specific OEM harness was qualified. */
};

struct starter_config {
    enum starter_profile profile;
    uint32_t contact_settle_ms; /* Commissioned release/operate time including coil suppression. */
    uint32_t start_pulse_ms;
    uint32_t stop_pulse_ms;
    enum starter_profile harness_profile; /* Read back from separately commissioned service configuration. */
    /* Selected cabinet guard, original hardwired STOP and overload are commissioned.
     * Earlier cabinet profiles also require the independent float LS1. */
    bool independent_shutdown;
    struct starter_pulse_range start_range, stop_range;
    uint32_t confirm_stop_ms; /* From the STOP request, including relay release, OEM response and coast. */
    uint32_t max_run_ms; /* Required by panel_controls: commissioned time limit for each HOST run. */
};

struct starter_outputs {
    struct starter_config config;
    enum starter_phase phase;
    enum starter_command previous;
    uint32_t since_ms, stop_requested_ms;
    bool host, healthy, armed;
};

struct starter_drive {
    bool arm_issued; /* One accepted arm event. Pulse GPIO17 only on this event. */
    bool permit_d; /* GPIO20 -> gated K1 / J30 (A). External ARM and STOP chain still apply. */
    bool run_cmd;  /* GPIO19 -> K2 / J35 (B). */
    bool start_issued, stop_issued; /* Edges for command_leds, not motor feedback. */
};

/* Initialize only while the starter is isolated and both outputs are off. */
bool starter_configure(struct starter_outputs *s, struct starter_config config);
enum starter_transfer starter_transfer_decode(bool host_n, bool local_n);

/* Single control task. Resolve competing input events to STOP before this call.
 * Use fresh, debounced HOST/LOCAL inputs. A read failure supplies TRANSFER_UNKNOWN.
 * healthy includes permission to run and a verified hardware latch clear after reset;
 * stopped requires valid, fresh feedback.
 * ARM is a fresh operator event. ACKNOWLEDGE is a separate local operator
 * edge, accepted only with the guard down, good independent stop feedback and
 * neutral controls. The caller qualifies that edge. A fault withdraws both
 * outputs and the caller must suppress the external guard heartbeat.
 * The caller applies the returned drive immediately, independently of the OLED/I²C. */
struct starter_drive starter_step(struct starter_outputs *s, uint32_t now_ms, enum starter_transfer position,
                                 bool healthy, bool stopped, enum starter_command command);

#ifdef __cplusplus
}
#endif
#endif
