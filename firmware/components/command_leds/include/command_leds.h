#ifndef PUMP_COMMAND_LEDS_H
#define PUMP_COMMAND_LEDS_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

enum pump_command_light {
    PUMP_LIGHT_OFF = 0,
    PUMP_LIGHT_START,
    PUMP_LIGHT_STOP
};

struct pump_command_leds {
    enum pump_command_light light;
    uint32_t started_ms;
};

/* Zero-initialize at boot and on entry to LOCAL MANUAL. Call from one task. */
/* Pass edge events after the control output has been commanded. */
void pump_command_leds_record(struct pump_command_leds *leds, uint32_t now_ms,
                              bool start_issued, bool stop_issued);

/* Merge into the expander owner's desired output latch bytes, A then B. */
void pump_command_leds_render(struct pump_command_leds *leds, uint32_t now_ms,
                              uint8_t olat[2]);

#ifdef __cplusplus
}
#endif
#endif
