#include "metered_gpio.h"
#include <string.h>

/* Three-byte header followed by 1..3 data bytes, MSB first under one CS. */
static esp_err_t transfer(spi_device_handle_t d, uint16_t reg, bool read, uint8_t *bytes, size_t length)
{
    uint8_t tx[6] = {(uint8_t)(reg >> 8), (uint8_t)reg, read ? 0x80 : 0};
    uint8_t rx[6] = {0};
    if (!read) memcpy(tx + 3, bytes, length);
    spi_transaction_t t = {.length = 8 * (length + 3), .tx_buffer = tx, .rx_buffer = rx};
    esp_err_t err = spi_device_polling_transmit(d, &t);
    if (read && err == ESP_OK) memcpy(bytes, rx + 3, length);
    return err;
}

static esp_err_t timing_valid(spi_device_handle_t d)
{
    uint8_t value[2];
    esp_err_t err = transfer(d, 0x120, true, value, sizeof(value));
    if (err != ESP_OK) return err;
    return value[0] == 0 && value[1] == 0x30 ? ESP_OK : ESP_ERR_INVALID_RESPONSE;
}

esp_err_t metered_spi_init(spi_device_handle_t *device)
{
    if (!device) return ESP_ERR_INVALID_ARG;
    *device = NULL;
    spi_bus_config_t bus = {.mosi_io_num = 7, .miso_io_num = 14, .sclk_io_num = 6,
                            .quadwp_io_num = -1, .quadhd_io_num = -1};
    spi_device_interface_config_t spec = {.clock_speed_hz = 1000000, .mode = 0,
                                         .spics_io_num = 18, .queue_size = 1};
    esp_err_t err = spi_bus_initialize(SPI2_HOST, &bus, SPI_DMA_DISABLED);
    if (err != ESP_OK) return err;
    spi_device_handle_t d = NULL;
    err = spi_bus_add_device(SPI2_HOST, &spec, &d);
    uint8_t unlock = 0xad, timing[] = {0, 0x30};
    if (err == ESP_OK) err = transfer(d, 0x0fe, false, &unlock, 1);
    if (err == ESP_OK) err = transfer(d, 0x120, false, timing, sizeof(timing));
    if (err == ESP_OK) err = timing_valid(d);
    if (err != ESP_OK) {
        if (d) spi_bus_remove_device(d);
        spi_bus_free(SPI2_HOST);
        return err;
    }
    *device = d;
    return ESP_OK;
}

esp_err_t metered_gpio_step(spi_device_handle_t d, struct panel_controls *p,
                            uint32_t now, struct panel_sample in, struct panel_result *out)
{
    uint8_t bytes[3];
    in.voltage = (struct voltage_sample){0};
    esp_err_t err = d && p->onboard_voltage_required ? timing_valid(d) : ESP_ERR_INVALID_STATE;
    if (err == ESP_OK) err = transfer(d, 0x21c, true, bytes, sizeof(bytes));
    if (err == ESP_OK) {
        in.voltage.counts = ((uint32_t)bytes[0] << 16) | ((uint32_t)bytes[1] << 8) | bytes[2];
        in.voltage.acquired_ms = now;
        in.voltage.valid = true;
    } else {
        in.process_healthy = false;
    }
    /* Deliver the stop decision even on SPI failure. The actuator task applies out->drive. */
    esp_err_t gpio_err = guard_gpio_step(p, now, in, out);
    return gpio_err != ESP_OK ? gpio_err : err;
}
