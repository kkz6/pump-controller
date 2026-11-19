#include "panel_controls.h"

/* Main U33 port B: START_N B0, SET/RESET_N B1, NC STOP closed B2, MODE B3,
 * NEXT B4, external guard auxiliary closed B5 and KEY_MAN_N B6.
 * Port A: KEY_AUTO_N A0, LOCAL_N A2 and HOST_N A3. */
enum { START = 1, SET = 2, MODE = 4, NEXT = 8 };
enum { KEY_MANUAL = 1, KEY_AUTO = 2 };

static uint8_t debounce(struct panel_debounce *input, uint8_t value, uint32_t now,
                        uint32_t delay, bool first)
{
    uint8_t old = input->stable;
    if (first || value != input->candidate) {
        input->candidate = value;
        input->since_ms = now;
    }
    if (first || now - input->since_ms >= delay) input->stable = value;
    return first ? 0 : input->stable & (uint8_t)~old;
}

bool panel_controls_configure(struct panel_controls *p, struct starter_config config,
                              bool key_fitted, uint32_t debounce_ms, uint32_t max_age_ms)
{
    *p = (struct panel_controls){0}; /* MANUAL, disarmed, no automatic permission. */
    if (!debounce_ms || debounce_ms > INT32_MAX || !max_age_ms || max_age_ms > GUARD_MAX_SAMPLE_AGE_MS)
        return false;
    p->key_fitted = key_fitted;
    p->debounce_ms = debounce_ms;
    p->max_age_ms = max_age_ms;
    return starter_configure(&p->outputs, config);
}

static void update_heartbeat(struct panel_controls *p, uint32_t now, const struct panel_sample *in,
                             bool healthy)
{
    if (!p->guard_clock_started || !healthy) {
        p->guard_clock_started = true;
        p->guard_quiet_since_ms = now;
        p->guard_last_edge_ms = now;
        p->guard_recovered = p->heartbeat_high = false;
        p->guard_panel_sample_ms = in->sampled_at_ms;
        p->guard_process_sample_ms = in->protection_checked_at_ms;
        return;
    }
    /* Ensure even a brief fault is long enough for the independent monitor and
     * onboard watchdog to release. Stale or repeated samples cannot make edges. */
    if (!p->guard_recovered && now - p->guard_quiet_since_ms < GUARD_QUIET_MS) return;
    if (in->sampled_at_ms == p->guard_panel_sample_ms ||
        in->protection_checked_at_ms == p->guard_process_sample_ms ||
        now - p->guard_last_edge_ms < GUARD_EDGE_MS) return;
    p->guard_recovered = true;
    p->heartbeat_high = !p->heartbeat_high;
    p->guard_last_edge_ms = now;
    p->guard_panel_sample_ms = in->sampled_at_ms;
    p->guard_process_sample_ms = in->protection_checked_at_ms;
}

struct panel_result panel_controls_step(struct panel_controls *p, uint32_t now, struct panel_sample in)
{
    struct panel_result result = {0};
    bool fresh = in.valid && now - in.sampled_at_ms <= p->max_age_ms;
    uint32_t gap = in.sampled_at_ms - p->last_sample_ms;
    if (p->initialized && gap > INT32_MAX) fresh = false;
    bool interrupted = p->initialized && gap > p->max_age_ms;
    bool process_fresh = now - in.protection_checked_at_ms <= p->max_age_ms;
    if (p->initialized && in.protection_checked_at_ms - p->last_process_ms > p->max_age_ms)
        process_fresh = false;
    p->last_process_ms = in.protection_checked_at_ms;
    if (fresh) p->last_sample_ms = in.sampled_at_ms;
    enum starter_transfer transfer = fresh
        ? starter_transfer_decode((in.gpio_a & 8) != 0, (in.gpio_a & 4) != 0) : TRANSFER_UNKNOWN;
    uint8_t raw = ((in.gpio_b & 1) ? 0 : START) | ((in.gpio_b & 2) ? 0 : SET)
                  | ((in.gpio_b & 8) ? MODE : 0) | ((in.gpio_b & 16) ? NEXT : 0);
    uint8_t key = ((in.gpio_b & 64) ? 0 : KEY_MANUAL) | ((in.gpio_a & 1) ? 0 : KEY_AUTO);
    bool first = !p->initialized || interrupted;
    /* Debounce on acquisition time; re-reading the same sample cannot mature an edge. */
    uint8_t pressed = debounce(&p->buttons, raw, in.sampled_at_ms, p->debounce_ms, first);
    debounce(&p->key, key, in.sampled_at_ms, p->debounce_ms, first);
    p->initialized = fresh;
    bool key_ok = !p->key_fitted ||
                  ((key == KEY_MANUAL || key == KEY_AUTO) && key == p->key.stable);
    bool healthy = fresh && !interrupted && process_fresh && in.process_healthy && key_ok && (in.gpio_b & 4);
    bool monitor_eligible = healthy && transfer == TRANSFER_HOST && p->outputs.config.profile != STARTER_DISABLED;
    enum panel_mode mode = p->mode;
    if (monitor_eligible) {
        if (p->key_fitted) mode = key == KEY_AUTO ? PANEL_AUTO : PANEL_MANUAL;
        else if (pressed & MODE) mode = mode == PANEL_AUTO ? PANEL_MANUAL : PANEL_AUTO;
    }
    bool mode_changed = mode != p->mode;
    p->mode = mode;
    update_heartbeat(p, now, &in, monitor_eligible && !mode_changed);
    result.heartbeat_high = p->heartbeat_high;
    /* The monitor must be able to qualify before the independent manual reset.
     * Only the separate guard contact on J31 permits an actual start. */
    bool ready = monitor_eligible && p->guard_recovered && (in.gpio_b & 32);
    /* Viewing settings or acknowledging a trip does not grant permission to run. */
    result.set_reset_pressed = fresh && (pressed & SET);
    result.set_reset_held = fresh && (p->buttons.stable & SET);
    result.next_pressed = fresh && (pressed & NEXT);
    bool editing = in.settings_open || ((raw | p->buttons.stable) & (SET | NEXT));
    enum starter_command command = STARTER_NONE;

    if (!ready || mode_changed) {
        /* Clear automatic permission even if the same demand or START stays asserted. */
        p->auto_enabled = p->pending_start = p->start_released = p->release_timing = false;
        command = STARTER_STOP;
    } else {
        if (!(raw & START) && !(p->buttons.stable & START)) {
            if (!p->release_timing) p->released_since_ms = in.sampled_at_ms;
            p->release_timing = true;
            if (in.sampled_at_ms - p->released_since_ms >= p->debounce_ms)
                p->start_released = true;
        } else {
            p->release_timing = false;
        }
        bool start = (pressed & START) && p->start_released;
        if (pressed & START) p->start_released = false;
        bool idle = p->outputs.phase == STARTER_IDLE;
        if (start && !editing && idle && in.motor_stopped && mode == PANEL_AUTO) {
            p->auto_enabled = true;
            p->demand_used = false;
        }
        if (mode == PANEL_AUTO && !in.fill_demand) {
            if (p->demand_used && (p->pending_start || !idle)) command = STARTER_STOP;
            p->pending_start = p->demand_used = false;
        }
        if (editing && in.fill_demand) p->demand_used = true;
        if (p->pending_start && (editing || !in.motor_stopped)) {
            p->pending_start = false;
            command = STARTER_STOP;
        } else if (p->pending_start && in.sampled_at_ms != p->arm_sample_ms) {
            command = STARTER_START;
            p->pending_start = false;
        } else if (!p->pending_start && !editing && idle && in.motor_stopped) {
            bool auto_start = mode == PANEL_AUTO && p->auto_enabled && in.fill_demand && !p->demand_used;
            if ((mode == PANEL_MANUAL && start) || auto_start) command = STARTER_ARM;
            if (auto_start) p->demand_used = true;
        }
    }
    result.drive = starter_step(&p->outputs, now, transfer, ready, in.motor_stopped, command);
    if (result.drive.arm_issued) {
        p->pending_start = true;
        p->arm_sample_ms = in.sampled_at_ms;
    }
    result.mode = mode;
    result.auto_enabled = p->auto_enabled;
    return result;
}
