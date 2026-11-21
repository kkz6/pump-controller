# USB programming and recovery

J40 is a native USB-C **data** port. An isolated, regulated 5 V bench supply at J41 powers the controller. Normal ESP-IDF flashing can request download mode over USB. The physical buttons also work with blank flash or an application that has disabled USB. [Espressif USB Serial/JTAG](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c6/api-guides/usb-serial-jtag-console.html)

| Main board marking | Connection | Purpose |
| --- | --- | --- |
| BOOT, SW60 | GPIO9 to GND while pressed | Select ROM download mode when EN rises. R21 holds GPIO9 high normally. R22 holds GPIO8 high for a valid download strap. |
| EN RESET, SW61 | CHIP_PU to GND while pressed | Hardware reset. R20 and C22 restore EN after release. |
| USB TX, D60 | Expander GPA2 through R260 | Device-to-host application transmission. |
| USB RX, D61 | Expander GPA3 through R261 | Host-to-device application reception. |

The ROM download sequence runs before application firmware. Watch the flashing tool on the computer for programming progress. The OLED panel’s SET/RESET button is an operator input available for an application pairing or settings-reset workflow. EN RESET restarts the processor and preserves flash. The bench image does not erase pairing data through either button. [ESP32-C6 boot mode selection](https://docs.espressif.com/projects/esptool/en/latest/esp32c6/advanced-topics/boot-mode-selection.html)

## First flash

1. Use a de-energized board on the bench. Disconnect mains J1 and the two starter plugs J30 and J35. With the RUN link removed, the BENCH plug supplies isolated +5 V at J41 pin 2 and GND at pin 3, leaving pin 1 empty. USB VBUS also removes the relay command supply in hardware.
2. Connect a USB data cable at J40. Hold **BOOT**, press and release **EN RESET**, then release **BOOT**. The ESP32-C6 ROM should enumerate. The OLED panel is unnecessary for this test.
3. From an ESP-IDF v5.4.2 environment, replace PORT with the actual serial device and run the command below at the repository root. This writes the supplied bench image, bootloader and partition table. The image is set for the 4 MB flash of the ESP32-C6-MINI-1U-H4. Preserve any firmware you need before programming.

   ```sh
   python -m esptool --chip esp32c6 --port PORT write_flash 0x0 manufacturing/usb-bench.bin
   ```

4. Release BOOT and tap EN RESET to return to the application if required. Open the USB serial port in a terminal. The bench app sends a greeting and echoes received bytes. TX lights after a transfer completes and RX lights after receiving bytes. Each indication lasts about 100 ms. The bench app holds the four starter-command and watchdog pins low.
5. Check recovery again from the running application by repeating step 2. Confirm USB enumeration, both plug orientations, TX/RX behavior and the inhibited relay supply on the physical prototype.

For a source build, run `idf.py set-target esp32c6` and `idf.py build merge-bin` in `firmware/bench`. The generated `build/merged-binary.bin` is the single-file image. The bench application uses the native USB Serial/JTAG driver, the two 5.1 kΩ USB-C configuration resistors and the board's data switch. Its indicator task owns I²C address 0x20 in MCP23017 BANK=0 mode and preserves the other port A outputs. A future pump application must serialize all expander writes through its shared owner, retain SW60/SW61 recovery, and call the activity indicator only for its own USB transfers.
