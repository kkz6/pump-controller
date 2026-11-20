#pragma once
#include <stdbool.h>
#include <stdint.h>

struct usb_activity {
    uint32_t last_tx_ms;
    uint32_t last_rx_ms;
    bool tx;
    bool rx;
};

/* Device perspective. Call with accepted RX bytes and completed TX transfers. */
uint8_t usb_activity_sample(struct usb_activity *state, uint32_t now_ms, bool tx, bool rx);
