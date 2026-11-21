#include "panel_controls.h"

/* Main U33 port B: START_N B0, SET/RESET_N B1, NC STOP closed B2, MODE B3,
 * NEXT B4, external guard auxiliary closed B5 and KEY_MAN_N B6.
 * Port A: KEY_AUTO_N A0. Cabinet boards read LOCAL_N A2 and HOST_N A3; on the
 * direct main board A2/A3 drive the USB TX/RX indicators and the direct profile
 * forces HOST, so it never decodes them. A1 and A4-A6 are unused: configure
 * them as inputs with GPPU enabled. */
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
    if (!config.max_run_ms || config.max_run_ms > INT32_MAX) return false;
    if (!debounce_ms || debounce_ms > INT32_MAX || !max_age_ms || max_age_ms > GUARD_MAX_SAMPLE_AGE_MS)
        return false;
    p->key_fitted = key_fitted;
    p->debounce_ms = debounce_ms;
    p->max_age_ms = max_age_ms;
    return starter_configure(&p->outputs, config);
}

static bool configure_voltage_control(struct panel_controls *p, struct starter_config config, bool key_fitted,
                         uint32_t debounce_ms, uint32_t max_age_ms, struct voltage_limits limits, bool direct)
{
    if ((!direct && config.profile != STARTER_OPEN_STOP) || !voltage_limits_valid(limits) ||
        !panel_controls_configure(p, config, key_fitted, debounce_ms, max_age_ms)) {
        *p = (struct panel_controls){0};
        return false;
    }
    p->direct_starter = direct;
    p->onboard_voltage_required = true;
    p->voltage_limits = limits;
    return true;
}

bool metered_dol_configure(struct panel_controls *p, struct starter_config config, bool key_fitted,
                          uint32_t debounce_ms, uint32_t max_age_ms, struct voltage_limits limits)
{
    return configure_voltage_control(p, config, key_fitted, debounce_ms, max_age_ms, limits, false);
}

bool direct_starter_configure(struct panel_controls *p, struct starter_config config, bool key_fitted,
                              uint32_t debounce_ms, uint32_t max_age_ms, struct voltage_limits limits)
{
    return configure_voltage_control(p, config, key_fitted, debounce_ms, max_age_ms, limits, true);
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

/* A held SET or a press begun before confirmed stop cannot acknowledge the timeout. */
static bool timeout_reset_pressed(struct panel_controls *p, bool eligible, uint8_t raw,
                                  uint8_t pressed, uint32_t sample_ms)
{
    if (!eligible) {
        p->timeout_set_released = p->timeout_set_timing = false;
    } else if (!((raw | p->buttons.stable) & SET)) {
        if (!p->timeout_set_timing) p->timeout_set_released_ms = sample_ms;
        p->timeout_set_timing = true;
        if (sample_ms - p->timeout_set_released_ms >= p->debounce_ms)
            p->timeout_set_released = true;
    } else {
        p->timeout_set_timing = false;
        if (p->timeout_set_released && (pressed & SET)) {
            p->timeout_set_released = false;
            return true;
        }
    }
    return false;
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
    /* The direct PCB has no cabinet position inputs. B5 still reads the actual
     * panel STOP return after USB inhibit and remains required for a start. */
    if (p->direct_starter && fresh) transfer = TRANSFER_HOST;
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
    /* A valid scan has consecutive wet electrodes starting at L1:
     * empty, L1, L1+L2, L1+L2+L3 or full. An invalid scan is a process fault. */
    bool previous_scan_recent = p->have_tank_scan && now - p->last_tank_scan_ms <= TANK_MAX_SCAN_AGE_MS;
    bool scan_fresh = now - in.tank_scanned_at_ms <= TANK_MAX_SCAN_AGE_MS &&
                      (!previous_scan_recent || in.tank_scanned_at_ms - p->last_tank_scan_ms <= INT32_MAX);
    bool tank_valid = in.tank_levels_valid && scan_fresh && in.tank_wet_mask <= 0x0F &&
                      (in.tank_wet_mask & (in.tank_wet_mask + 1u)) == 0;
    if (tank_valid) {
        p->have_tank_scan = true;
        p->last_tank_scan_ms = in.tank_scanned_at_ms;
    }
    bool low = tank_valid && in.tank_wet_mask == 0;
    bool full = tank_valid && in.tank_wet_mask == 0x0F;
    bool voltage_ok = true;
    if (p->onboard_voltage_required) {
        result.voltage_status = voltage_update(&p->voltage_window, p->voltage_limits,
                                               in.voltage, now, p->max_age_ms);
        result.mains_mv = p->voltage_window.millivolts;
        voltage_ok = result.voltage_status == VOLTAGE_OK;
    }
    bool healthy = voltage_ok && fresh && !interrupted && process_fresh && in.process_healthy &&
                   tank_valid && key_ok && (in.gpio_b & 4);
    bool monitor_eligible = healthy && transfer == TRANSFER_HOST && p->outputs.config.profile != STARTER_DISABLED;
    enum panel_mode mode = p->mode;
    if (monitor_eligible) {
        if (p->key_fitted) mode = key == KEY_AUTO ? PANEL_AUTO : PANEL_MANUAL;
        else if (pressed & MODE) mode = mode == PANEL_AUTO ? PANEL_MANUAL : PANEL_AUTO;
    }
    bool mode_changed = mode != p->mode;
    p->mode = mode;
    bool faulted = p->outputs.phase == STARTER_FEEDBACK_FAULT;
    update_heartbeat(p, now, &in, monitor_eligible && !mode_changed && !faulted);
    /* The monitor must be able to qualify before the independent manual reset.
     * An actual start requires feedback from the commissioned cabinet guard. */
    bool ready = monitor_eligible && p->guard_recovered && (in.gpio_b & 32);
    /* Viewing settings or acknowledging a trip does not grant permission to run. */
    result.set_reset_pressed = fresh && (pressed & SET);
    result.set_reset_held = fresh && (p->buttons.stable & SET);
    result.next_pressed = fresh && (pressed & NEXT);
    bool editing = in.settings_open || ((raw | p->buttons.stable) & (SET | NEXT));
    enum starter_command command = STARTER_NONE;

    bool filling = p->outputs.phase == STARTER_PERMISSION || p->outputs.phase == STARTER_STARTING ||
                   p->outputs.phase == STARTER_RUNNING;
    if (filling && now - p->run_started_ms >= p->outputs.config.max_run_ms)
        p->run_timed_out = true;

    if (!ready || mode_changed || p->run_timed_out) {
        /* Clear automatic permission even if the same demand or START stays asserted. */
        p->auto_enabled = p->pending_start = p->start_released = p->release_timing = false;
        command = STARTER_STOP;
        bool reset_eligible = ready && p->outputs.phase == STARTER_IDLE && in.motor_stopped &&
                              !((raw | p->buttons.stable) & START);
        if (p->run_timed_out && timeout_reset_pressed(p, reset_eligible, raw, pressed, in.sampled_at_ms))
            p->run_timed_out = false;
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
        if (full) {
            if (p->outputs.armed || p->pending_start) command = STARTER_STOP;
            p->pending_start = false;
            /* AUTO may be enabled in standby at full, without energizing either relay. */
            p->demand_used = in.fill_demand;
        } else if (p->pending_start && (editing || !in.motor_stopped || (mode == PANEL_AUTO && !low))) {
            p->pending_start = false;
            command = STARTER_STOP;
        } else if (p->pending_start && in.sampled_at_ms != p->arm_sample_ms) {
            command = STARTER_START;
            p->pending_start = false;
        } else if (!p->pending_start && !editing && idle && in.motor_stopped) {
            bool auto_start = mode == PANEL_AUTO && p->auto_enabled && low && in.fill_demand && !p->demand_used;
            if ((mode == PANEL_MANUAL && start) || auto_start) command = STARTER_ARM;
            if (auto_start) p->demand_used = true;
        }
    }
    bool confirmed_stopped = fresh && !interrupted && process_fresh && in.process_healthy && in.motor_stopped;
    /* An actual post-trip SET edge is required. Confirm the external guard
     * has dropped before accepting it, and keep START and automatic demand
     * disarmed through the normal external RESET/ENABLE procedure. */
    if (faulted && monitor_eligible && (p->direct_starter || !(in.gpio_b & 32)) && confirmed_stopped &&
        !(raw & START) && !(p->buttons.stable & START) && (pressed & SET))
        command = STARTER_ACKNOWLEDGE;
    /* Direct-board B5 follows the panel STOP loop. A deliberate neutral SET
     * after confirmed stop may clear a fault while keeping drive disarmed. */
    result.drive = starter_step(&p->outputs, now, transfer, ready && command != STARTER_ACKNOWLEDGE,
                                confirmed_stopped, command);
    if (p->direct_starter && p->outputs.config.profile == STARTER_RUN_PAIR)
        result.drive.run_cmd = false; /* A alone drives a documented maintained RUN input. */
    /* Start once at acceptance, including permission settling and start pulses.
     * Repeated samples, changing demand and phase changes never extend a run. */
    if (command == STARTER_START && (result.drive.start_issued || p->outputs.phase == STARTER_PERMISSION))
        p->run_started_ms = now;
    result.run_timed_out = p->run_timed_out;
    result.feedback_fault = p->outputs.phase == STARTER_FEEDBACK_FAULT;
    if (result.feedback_fault && !faulted) {
        update_heartbeat(p, now, &in, false);
        p->auto_enabled = p->pending_start = p->start_released = p->release_timing = false;
    }
    result.heartbeat_high = p->heartbeat_high;
    if (result.drive.arm_issued) {
        p->pending_start = true;
        p->arm_sample_ms = in.sampled_at_ms;
    }
    result.mode = mode;
    result.auto_enabled = p->auto_enabled;
    return result;
}
