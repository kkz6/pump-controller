idf_component_register(SRCS "starter_outputs.c" "panel_controls.c" "guard_gpio.c" "onboard_voltage.c" "metered_gpio.c"
                       INCLUDE_DIRS "include" REQUIRES esp_driver_gpio esp_driver_spi)
