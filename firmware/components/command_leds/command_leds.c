#include "command_leds.h"

enum { PULSE_MS = 250, LED_BIT = 0x80 };

void pump_command_leds_record(struct pump_command_leds *leds, uint32_t now_ms,
                              bool start_issued, bool stop_issued)
{
    if (!start_issued && !stop_issued) {
        return;
    }
    leds->light = stop_issued ? PUMP_LIGHT_STOP : PUMP_LIGHT_START;
    leds->started_ms = now_ms;
}

void pump_command_leds_render(struct pump_command_leds *leds, uint32_t now_ms,
                              uint8_t olat[2])
{
    if ((uint32_t)(now_ms - leds->started_ms) >= PULSE_MS) {
        leds->light = PUMP_LIGHT_OFF;
    }
    /* GPA7 drives red STOP. GPB7 drives green START. Other pins are shared. */
    olat[0] &= (uint8_t)~LED_BIT;
    olat[1] &= (uint8_t)~LED_BIT;
    if (leds->light == PUMP_LIGHT_STOP) {
        olat[0] |= LED_BIT;
    } else if (leds->light == PUMP_LIGHT_START) {
        olat[1] |= LED_BIT;
    }
}
