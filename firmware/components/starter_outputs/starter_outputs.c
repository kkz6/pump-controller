#include "starter_outputs.h"

static bool duration_valid(uint32_t ms)
{
    return ms > 0 && ms <= INT32_MAX;
}

bool starter_configure(struct starter_outputs *s, struct starter_config config)
{
    *s = (struct starter_outputs){0};
    if (!duration_valid(config.contact_settle_ms)) return false;
    switch (config.profile) {
    case STARTER_RUN_PAIR:
        break;
    case STARTER_OPEN_STOP:
        if (!duration_valid(config.start_pulse_ms)) return false;
        break;
    case STARTER_PULSE_STOP:
        if (!duration_valid(config.start_pulse_ms) || !duration_valid(config.stop_pulse_ms)
            || !config.independent_shutdown) return false;
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
        if (elapsed >= s->config.contact_settle_ms) enter(s, STARTER_IDLE, now);
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
