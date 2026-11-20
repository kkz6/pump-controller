#include "driver/gpio.h"
#include "driver/i2c_master.h"
#include "driver/usb_serial_jtag.h"
#include "esp_check.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "usb_activity.h"

enum { IODIRA = 0x00, OLATA = 0x14, ACTIVITY_MASK = 0x0c };
static const uint8_t banner[] = "Pump controller USB bench. Starter outputs disabled. Type to echo.\r\n";

/* This task owns MCP23017 on the bench. Preserve the other six port-A bits. */
static esp_err_t update_bits(i2c_master_dev_handle_t io, uint8_t reg, uint8_t bits)
{
    uint8_t old;
    esp_err_t err = i2c_master_transmit_receive(io, &reg, 1, &old, 1, 20);
    if (err != ESP_OK) return err;
    uint8_t cmd[] = { reg, (uint8_t)((old & ~ACTIVITY_MASK) | (bits & ACTIVITY_MASK)) };
    return i2c_master_transmit(io, cmd, sizeof(cmd), 20);
}

static void disable_starter(void)
{
    const gpio_num_t outputs[] = { GPIO_NUM_17, GPIO_NUM_19, GPIO_NUM_20, GPIO_NUM_21 };
    uint64_t mask = 0;
    for (size_t i = 0; i < sizeof(outputs) / sizeof(outputs[0]); ++i) {
        ESP_ERROR_CHECK(gpio_set_level(outputs[i], 0));
        mask |= 1ULL << outputs[i];
    }
    const gpio_config_t config = { .pin_bit_mask = mask, .mode = GPIO_MODE_OUTPUT };
    ESP_ERROR_CHECK(gpio_config(&config));
}

void app_main(void)
{
    disable_starter();
    usb_serial_jtag_driver_config_t usb = { .tx_buffer_size = 512, .rx_buffer_size = 512 };
    ESP_ERROR_CHECK(usb_serial_jtag_driver_install(&usb));

    i2c_master_bus_handle_t bus;
    i2c_master_dev_handle_t io;
    const i2c_master_bus_config_t cfg = {
        .i2c_port = I2C_NUM_0, .sda_io_num = GPIO_NUM_22, .scl_io_num = GPIO_NUM_23,
        .clk_source = I2C_CLK_SRC_DEFAULT, .glitch_ignore_cnt = 7
    };
    const i2c_device_config_t dev = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7, .device_address = 0x20, .scl_speed_hz = 100000
    };
    bool have_io = i2c_new_master_bus(&cfg, &bus) == ESP_OK &&
                   i2c_master_bus_add_device(bus, &dev, &io) == ESP_OK;
    bool initialized = false, tx_pending = false, greeted = false;
    uint8_t shown = 0, buffer[64];
    const uint8_t *pending = buffer;
    size_t remaining = 0;
    struct usb_activity activity = {0};
    for (;;) {
        int received = 0;
        bool connected = usb_serial_jtag_is_connected();
        if (!connected) {
            greeted = false;
            tx_pending = false;
            remaining = 0;
            vTaskDelay(pdMS_TO_TICKS(10));
        } else {
            if (remaining == 0 && !greeted) {
                pending = banner;
                remaining = sizeof(banner) - 1;
                greeted = true;
            } else if (remaining == 0) {
                received = usb_serial_jtag_read_bytes(buffer, sizeof(buffer), pdMS_TO_TICKS(10));
                if (received > 0) {
                    pending = buffer;
                    remaining = (size_t)received;
                }
            }
            if (remaining > 0) {
                int written = usb_serial_jtag_write_bytes(pending, remaining, pdMS_TO_TICKS(10));
                if (written > 0) {
                    pending += written;
                    remaining -= (size_t)written;
                    tx_pending = true;
                }
            }
        }
        bool sent = tx_pending && usb_serial_jtag_wait_tx_done(0) == ESP_OK;
        if (sent) tx_pending = false;
        uint8_t next = usb_activity_sample(&activity, (uint32_t)(esp_timer_get_time() / 1000), sent, received > 0);
        if (have_io && !initialized) {
            initialized = update_bits(io, OLATA, 0) == ESP_OK && update_bits(io, IODIRA, 0) == ESP_OK;
            shown = 0;
        }
        if (initialized && next != shown && update_bits(io, OLATA, next) == ESP_OK) shown = next;
    }
}
