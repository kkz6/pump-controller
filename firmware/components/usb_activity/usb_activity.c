#include "usb_activity.h"

enum { PULSE_MS = 100, TX_BIT = 1U << 2, RX_BIT = 1U << 3 };

uint8_t usb_activity_sample(struct usb_activity *state, uint32_t now_ms, bool tx, bool rx)
{
    if (tx) state->last_tx_ms = now_ms;
    if (rx) state->last_rx_ms = now_ms;
    state->tx = tx || (state->tx && now_ms - state->last_tx_ms < PULSE_MS);
    state->rx = rx || (state->rx && now_ms - state->last_rx_ms < PULSE_MS);
    return (state->tx ? TX_BIT : 0) | (state->rx ? RX_BIT : 0);
}
