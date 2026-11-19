#ifndef PUMP_GUARD_GPIO_H
#define PUMP_GUARD_GPIO_H

#include "esp_err.h"
#include "panel_controls.h"

/* Initialize once, before enabling relays. Use this entry point in the ESP32-C6
 * control task. On an error, withdraw both relay requests and latch a fault. */
esp_err_t guard_gpio_init(void);
esp_err_t guard_gpio_step(struct panel_controls *panel, uint32_t now_ms,
                          struct panel_sample sample, struct panel_result *result);

#endif
