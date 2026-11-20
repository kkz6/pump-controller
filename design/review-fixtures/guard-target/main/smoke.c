#include "metered_gpio.h"
void app_main(void) {
    struct panel_controls panel;
    struct panel_result result;
    const struct starter_config disabled = {0};
    (void)panel_controls_configure(&panel, disabled, false, 10, 20);
    /* With no calibration or starter selection the metered configuration must stay disabled. */
    if (direct_starter_configure(&panel, disabled, false, 10, 20, (struct voltage_limits){0})) {
        spi_device_handle_t meter = NULL;
        if (metered_spi_init(&meter) == ESP_OK)
            (void)metered_gpio_step(meter, &panel, 0, (struct panel_sample){0}, &result);
    }
    if (guard_gpio_init() == ESP_OK)
        (void)guard_gpio_step(&panel, 0, (struct panel_sample){0}, &result);
}
