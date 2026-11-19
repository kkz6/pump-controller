#ifndef PUMP_PANEL_CONTROLS_H
#define PUMP_PANEL_CONTROLS_H

#include "starter_outputs.h"

#ifdef __cplusplus
extern "C" {
#endif

enum panel_mode { PANEL_MANUAL, PANEL_AUTO };

/* Independent field monitor observes rising edges at nominal 5 Hz. */
enum { GUARD_EDGE_MS = 100, GUARD_QUIET_MS = 3000, GUARD_MAX_SAMPLE_AGE_MS = 100 };

struct panel_sample {
    uint8_t gpio_a, gpio_b; /* Physical GPIO registers of main U33, IPOL=0. */
    uint32_t sampled_at_ms;
    uint32_t protection_checked_at_ms; /* Last complete evaluation of sensor freshness and trips. */
    bool valid; /* Both port reads and input-direction configuration verified. */
    bool process_healthy; /* Fresh protection inputs; independent of J31 guard feedback. */
    bool motor_stopped; /* Confirmed, fresh feedback; false also represents unknown. */
    bool fill_demand; /* Qualified automatic fill demand from the application. */
    bool settings_open;
};

struct panel_debounce {
    uint8_t candidate, stable;
    uint32_t since_ms;
};

struct panel_controls {
    struct starter_outputs outputs;
    struct panel_debounce buttons, key;
    enum panel_mode mode;
    uint32_t debounce_ms, max_age_ms, released_since_ms, arm_sample_ms, last_sample_ms;
    uint32_t guard_quiet_since_ms, guard_last_edge_ms, guard_panel_sample_ms, guard_process_sample_ms;
    uint32_t last_process_ms;
    bool guard_clock_started, guard_recovered, heartbeat_high;
    bool key_fitted, initialized, auto_enabled, demand_used, pending_start;
    bool release_timing, start_released;
};

struct panel_result {
    struct starter_drive drive;
    bool heartbeat_high; /* GPIO21 output level from this control cycle. Never use a free-running timer. */
    enum panel_mode mode;
    bool auto_enabled;
    bool set_reset_pressed, set_reset_held, next_pressed; /* OLED/settings events. */
};

/* Initialize with the pump stopped and starter outputs isolated. Use one control
 * task and commissioning-specific debounce, freshness and contact timings.
 * MANUAL START requests ARM and then START on distinct fresh samples.
 * AUTO START enables automatic filling; it starts only on qualified fill demand.
 * A physical STOP, change of mode, invalid transfer or loss of protection clears
 * that authorization until START is deliberately pressed again. The caller can
 * use the separate SET/RESET event to acknowledge a fault; it never clears a
 * live trip here. This instance is the sole owner of its starter sequencer. */
bool panel_controls_configure(struct panel_controls *panel, struct starter_config starter,
                              bool key_fitted, uint32_t debounce_ms, uint32_t max_age_ms);
struct panel_result panel_controls_step(struct panel_controls *panel, uint32_t now_ms,
                                        struct panel_sample sample);

#ifdef __cplusplus
}
#endif
#endif
