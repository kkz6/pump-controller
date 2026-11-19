#include "starter_outputs.h"

/* Supported momentary-control envelope. Commission narrower limits for each
 * input, including the electronic starter's long-press/settings threshold. */
static bool pulse_valid(uint32_t ms, struct starter_pulse_range range)
{
    return range.min_ms > 0 && range.min_ms <= ms && ms <= range.max_ms && range.max_ms <= 5000;
}

bool starter_configure(struct starter_outputs *s, struct starter_config config)
{
    *s = (struct starter_outputs){0};
    if (!config.independent_shutdown || config.profile != config.harness_profile ||
        !config.contact_settle_ms || config.contact_settle_ms > 1000 ||
        config.confirm_stop_ms <= config.contact_settle_ms || config.confirm_stop_ms > 30000) return false;
    switch (config.profile) {
    case STARTER_RUN_PAIR:
        break;
    case STARTER_OPEN_STOP:
        if (!pulse_valid(config.start_pulse_ms, config.start_range)) return false;
        break;
    case STARTER_PULSE_STOP:
        if (!pulse_valid(config.start_pulse_ms, config.start_range) ||
            !pulse_valid(config.stop_pulse_ms, config.stop_range) ||
            config.confirm_stop_ms <= 2 * config.contact_settle_ms + config.stop_pulse_ms) return false;
        break;
    default:
        return false;
    }
    s->config = config;
    return true;
}

static void enter(struct starter_outputs *s, enum starter_phase phase, uint32_t now)
{
    s->phase = phase;
    s->since_ms = now;
}

enum starter_transfer starter_transfer_decode(bool host_n, bool local_n)
{
    if (host_n == local_n) return TRANSFER_UNKNOWN;
    return host_n ? TRANSFER_LOCAL : TRANSFER_HOST;
}

struct starter_drive starter_step(struct starter_outputs *s, uint32_t now, enum starter_transfer position,
                                 bool healthy, bool stopped, enum starter_command command)
{
    struct starter_drive drive = {0};
    const enum starter_profile profile = s->config.profile;
    const bool host = position == TRANSFER_HOST;
    const bool new_host = host && !s->host;
    const bool lost_health = !healthy && s->healthy;
    const bool edge = command != s->previous;
    s->previous = command;
    s->host = host;
    s->healthy = healthy;

    if (s->phase == STARTER_FEEDBACK_FAULT) {
        if (host && stopped && !healthy && edge && command == STARTER_ACKNOWLEDGE)
            enter(s, STARTER_IDLE, now);
        return drive;
    }

    if (!host || profile == STARTER_DISABLED) {
        s->armed = false;
        enter(s, STARTER_IDLE, now);
        return drive;
    }

    const bool stopping = s->phase == STARTER_RELEASING || s->phase == STARTER_STOPPING
                          || s->phase == STARTER_SETTLING;
    if (new_host || lost_health || (command == STARTER_STOP && edge)) {
        s->armed = false;
        if (!stopping || new_host) {
            s->stop_requested_ms = now;
            /* Drop START first. An accepted pulse-STOP panel may still be running
             * on its own supply when the controller starts or recovers. */
            if (profile == STARTER_PULSE_STOP) {
                enter(s, STARTER_RELEASING, now);
            } else {
                drive.stop_issued = !new_host;
                enter(s, STARTER_SETTLING, now);
            }
        }
    } else if (!stopping && s->phase == STARTER_IDLE && edge && healthy && stopped) {
        if (command == STARTER_ARM && !s->armed) {
            s->armed = true;
            drive.arm_issued = true;
        } else if (command == STARTER_START && s->armed) {
            if (profile == STARTER_OPEN_STOP) {
                enter(s, STARTER_PERMISSION, now);
            } else {
                enter(s, profile == STARTER_RUN_PAIR ? STARTER_RUNNING : STARTER_STARTING, now);
                drive.start_issued = true;
            }
        }
    }

    const uint32_t elapsed = now - s->since_ms;
    const bool confirming = s->phase == STARTER_RELEASING || s->phase == STARTER_STOPPING ||
                            s->phase == STARTER_SETTLING;
    if ((confirming && !stopped && now - s->stop_requested_ms >= s->config.confirm_stop_ms) ||
        (s->phase == STARTER_PERMISSION && !stopped)) {
        s->armed = false;
        enter(s, STARTER_FEEDBACK_FAULT, now);
        return drive;
    }
    switch (s->phase) {
    case STARTER_PERMISSION:
        if (elapsed >= s->config.contact_settle_ms) {
            enter(s, STARTER_STARTING, now);
            drive.start_issued = true;
        }
        break;
    case STARTER_STARTING:
        if (elapsed >= s->config.start_pulse_ms) enter(s, STARTER_RUNNING, now);
        break;
    case STARTER_RELEASING:
        if (elapsed >= s->config.contact_settle_ms) {
            enter(s, STARTER_STOPPING, now);
            drive.stop_issued = true;
        }
        break;
    case STARTER_STOPPING:
        if (elapsed >= s->config.stop_pulse_ms) enter(s, STARTER_SETTLING, now);
        break;
    case STARTER_SETTLING:
        if (stopped && elapsed >= s->config.contact_settle_ms) enter(s, STARTER_IDLE, now);
        break;
    default:
        break;
    }

    if (profile == STARTER_RUN_PAIR) {
        drive.permit_d = s->phase == STARTER_RUNNING;
        drive.run_cmd = drive.permit_d;
    } else if (profile == STARTER_OPEN_STOP) {
        drive.permit_d = s->phase == STARTER_PERMISSION || s->phase == STARTER_STARTING
                         || s->phase == STARTER_RUNNING;
        drive.run_cmd = s->phase == STARTER_STARTING;
    } else {
        drive.permit_d = s->phase == STARTER_STARTING;
        drive.run_cmd = s->phase == STARTER_STOPPING;
    }
    return drive;
}
