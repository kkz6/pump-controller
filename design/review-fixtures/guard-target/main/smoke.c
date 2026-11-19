#include "guard_gpio.h"
void app_main(void) {
    struct panel_controls panel;
    struct panel_result result;
    const struct starter_config disabled = {0};
    (void)panel_controls_configure(&panel, disabled, false, 10, 20);
    if (guard_gpio_init() == ESP_OK)
        (void)guard_gpio_step(&panel, 0, (struct panel_sample){0}, &result);
}
