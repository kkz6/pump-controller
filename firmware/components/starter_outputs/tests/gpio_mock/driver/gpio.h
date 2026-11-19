/* ESP-IDF GPIO calls exercised by guard_gpio.c; no physical pins on this host. */
#ifndef TEST_DRIVER_GPIO_H
#define TEST_DRIVER_GPIO_H
#include <stdint.h>
#include "esp_err.h"
typedef struct { uint64_t pin_bit_mask; int mode, pull_up_en, pull_down_en, intr_type; } gpio_config_t;
enum { GPIO_NUM_21=21, GPIO_MODE_OUTPUT=2, GPIO_PULLUP_DISABLE=0, GPIO_PULLDOWN_DISABLE=0, GPIO_INTR_DISABLE=0 };
esp_err_t gpio_set_level(int pin, uint32_t level);
esp_err_t gpio_config(const gpio_config_t *config);
#endif
