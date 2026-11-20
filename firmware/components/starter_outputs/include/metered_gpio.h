#ifndef PUMP_METERED_GPIO_H
#define PUMP_METERED_GPIO_H
#include "driver/spi_master.h"
#include "guard_gpio.h"

/* Single owner, SPI2 on U3, mode 0, 1 MHz. Call after the U10 startup interval;
 * GPIO init and metered_dol_configure must also succeed before arming. */
esp_err_t metered_spi_init(spi_device_handle_t *device);
esp_err_t metered_gpio_step(spi_device_handle_t device, struct panel_controls *panel,
                            uint32_t now_ms, struct panel_sample sample, struct panel_result *result);
#endif
