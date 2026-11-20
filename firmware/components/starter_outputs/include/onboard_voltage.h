#ifndef PUMP_ONBOARD_VOLTAGE_H
#define PUMP_ONBOARD_VOLTAGE_H
#include <stdbool.h>
#include <stdint.h>

struct voltage_limits {
    uint32_t low_mv, high_mv, hysteresis_mv, recovery_ms;
    uint32_t reference_mv, reference_counts; /* Paired true-RMS reference and U10 VRMS reading. */
};

struct voltage_sample { uint32_t counts, acquired_ms; bool valid; };
enum voltage_status { VOLTAGE_UNAVAILABLE, VOLTAGE_LOW, VOLTAGE_HIGH, VOLTAGE_RECOVERING, VOLTAGE_OK };
struct voltage_window {
    uint32_t previous_ms, recovery_since_ms, millivolts;
    bool have_sample, recovering, allowed;
};

bool voltage_limits_valid(struct voltage_limits limits);
enum voltage_status voltage_update(struct voltage_window *window, struct voltage_limits limits,
                                   struct voltage_sample sample, uint32_t now, uint32_t max_age_ms);
#endif
