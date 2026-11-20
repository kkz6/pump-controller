#include "usb_activity.h"
#include <assert.h>
#include <stdint.h>

int main(void)
{
    struct usb_activity s = {0};
    assert(usb_activity_sample(&s, 0, false, false) == 0);
    assert(usb_activity_sample(&s, UINT32_MAX - 20, true, false) == 0x04);
    assert(usb_activity_sample(&s, 5, false, true) == 0x0c);
    assert(usb_activity_sample(&s, 79, false, false) == 0x08);
    assert(usb_activity_sample(&s, 105, false, false) == 0);
    assert(usb_activity_sample(&s, 200, true, true) == 0x0c);
    assert(usb_activity_sample(&s, 275, false, true) == 0x0c);
    assert(usb_activity_sample(&s, 300, false, false) == 0x08);
    return 0;
}
