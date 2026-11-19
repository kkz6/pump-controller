#include "guard_gpio.h"
#include "driver/gpio.h"

esp_err_t guard_gpio_init(void)
{
    esp_err_t status = gpio_set_level(GPIO_NUM_21, 0);
    if (status != ESP_OK) return status;
    const gpio_config_t config = {
        .pin_bit_mask = 1ULL << GPIO_NUM_21,
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE
    };
    return gpio_config(&config);
}

esp_err_t guard_gpio_step(struct panel_controls *panel, uint32_t now_ms,
                          struct panel_sample sample, struct panel_result *result)
{
    *result = panel_controls_step(panel, now_ms, sample);
    esp_err_t status = gpio_set_level(GPIO_NUM_21, result->heartbeat_high);
    if (status != ESP_OK) {
        *result = (struct panel_result){0};
        sample.valid = false;
        (void)panel_controls_step(panel, now_ms, sample);
        (void)gpio_set_level(GPIO_NUM_21, 0);
    }
    return status;
}
