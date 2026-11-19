#include "command_leds.h"
#include <assert.h>

static void expect_latches(struct pump_command_leds *leds, uint32_t now_ms,
                           uint8_t expected_a, uint8_t expected_b)
{
    /* The non-LED bits exercise preservation of the expander's other pins. */
    uint8_t olat[] = {0xd5, 0xaa};
    pump_command_leds_render(leds, now_ms, olat);
    assert(olat[0] == expected_a && olat[1] == expected_b);
}

int main(void)
{
    struct pump_command_leds leds = {0};
    expect_latches(&leds, 0, 0x55, 0x2a);
    pump_command_leds_record(&leds, 1000, true, false);
    expect_latches(&leds, 1000, 0x55, 0xaa);
    pump_command_leds_record(&leds, 1001, false, false);
    expect_latches(&leds, 1200, 0x55, 0xaa);

    pump_command_leds_record(&leds, 1210, true, true);
    expect_latches(&leds, 1459, 0xd5, 0x2a);
    expect_latches(&leds, 1460, 0x55, 0x2a);

    pump_command_leds_record(&leds, UINT32_MAX - 99, false, true);
    expect_latches(&leds, 149, 0xd5, 0x2a);
    expect_latches(&leds, 150, 0x55, 0x2a);
    return 0;
}
