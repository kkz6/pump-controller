#include "onboard_voltage.h"

enum { VRMS_FULL_SCALE_SINE = 9032007, VRMS_MAX_CODE = 0xffffff };

bool voltage_limits_valid(struct voltage_limits l)
{
    /* U10's usable analog range must include the high cutoff. Both the reference
     * point and practical upper limit must also be checked on the assembled input. */
    return l.low_mv >= 85000 && l.high_mv <= 264000 && l.hysteresis_mv && l.high_mv > l.low_mv &&
           2ULL * l.hysteresis_mv < l.high_mv - l.low_mv &&
           l.reference_counts && l.reference_counts < VRMS_FULL_SCALE_SINE &&
           l.reference_mv >= l.low_mv && l.reference_mv <= l.high_mv &&
           (uint64_t)l.high_mv * l.reference_counts < (uint64_t)VRMS_FULL_SCALE_SINE * l.reference_mv &&
           l.recovery_ms && l.recovery_ms <= INT32_MAX;
}

enum voltage_status voltage_update(struct voltage_window *w, struct voltage_limits l,
                                   struct voltage_sample s, uint32_t now, uint32_t max_age_ms)
{
    if (!voltage_limits_valid(l) || !s.valid || s.counts >= VRMS_MAX_CODE || now - s.acquired_ms > max_age_ms ||
        (w->have_sample && s.acquired_ms - w->previous_ms > INT32_MAX)) {
        *w = (struct voltage_window){0};
        return VOLTAGE_UNAVAILABLE;
    }
    if (!w->have_sample || s.acquired_ms - w->previous_ms > max_age_ms) {
        w->allowed = w->recovering = false;
    }
    w->have_sample = true;
    w->previous_ms = s.acquired_ms;
    uint64_t mv = ((uint64_t)s.counts * l.reference_mv + l.reference_counts / 2) / l.reference_counts;
    w->millivolts = mv > UINT32_MAX ? UINT32_MAX : (uint32_t)mv;
    if (mv <= l.low_mv || mv >= l.high_mv || s.counts >= VRMS_FULL_SCALE_SINE) {
        w->allowed = w->recovering = false;
        return mv <= l.low_mv ? VOLTAGE_LOW : VOLTAGE_HIGH;
    }
    if (w->allowed) return VOLTAGE_OK;
    if (mv >= l.low_mv + l.hysteresis_mv && mv <= l.high_mv - l.hysteresis_mv) {
        if (!w->recovering) w->recovery_since_ms = s.acquired_ms;
        w->recovering = true;
        w->allowed = s.acquired_ms - w->recovery_since_ms >= l.recovery_ms;
    } else {
        w->recovering = false;
    }
    return w->allowed ? VOLTAGE_OK : VOLTAGE_RECOVERING;
}
