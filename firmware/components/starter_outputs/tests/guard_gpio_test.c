#include "guard_gpio.h"
#include "driver/gpio.h"
#include <assert.h>

static bool initialized, line, fail_once;

esp_err_t gpio_set_level(int pin, uint32_t value)
{
    assert(pin == GPIO_NUM_21);
    if (fail_once) { fail_once = false; return ESP_FAIL; }
    if (!initialized) assert(!value);
    line = value != 0;
    return ESP_OK;
}

esp_err_t gpio_config(const gpio_config_t *cfg)
{
    assert(!line && cfg->pin_bit_mask == (1ULL << 21) && cfg->mode == GPIO_MODE_OUTPUT);
    initialized = true;
    return ESP_OK;
}

int main(void)
{
    struct panel_controls panel;
    const struct starter_config cfg = {.profile=STARTER_RUN_PAIR, .harness_profile=STARTER_RUN_PAIR,
        .start_range={5,100}, .stop_range={5,100}, .confirm_stop_ms=150, .max_run_ms=60000,
        .contact_settle_ms=10, .independent_shutdown=true};
    assert(panel_controls_configure(&panel, cfg, false, 5, 20));
    struct panel_sample sample = {.gpio_a=5,.gpio_b=103,.valid=true,.process_healthy=true, .tank_levels_valid=true,.motor_stopped=true};
    struct panel_result result;
    fail_once = true;
    assert(guard_gpio_init() == ESP_FAIL && !initialized);
    assert(guard_gpio_init() == ESP_OK && initialized && !line);
    for (uint32_t now=0; now<=GUARD_QUIET_MS; now+=10) {
        sample.tank_scanned_at_ms = sample.protection_checked_at_ms = sample.sampled_at_ms = now;
        assert(guard_gpio_step(&panel,now,sample,&result) == ESP_OK);
        assert(line == result.heartbeat_high && line == (now == GUARD_QUIET_MS));
    }
    fail_once = true;
    assert(guard_gpio_step(&panel,GUARD_QUIET_MS,sample,&result) == ESP_FAIL);
    assert(!line && !panel.guard_recovered && !result.drive.permit_d && !result.drive.run_cmd);
}
