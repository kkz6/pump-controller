#include "metered_gpio.h"
#include "driver/gpio.h"
#include <assert.h>

static uint32_t counts = 5750000;
static bool unlocked, timing, fail_read, attached;
static int bus;
esp_err_t spi_bus_initialize(int host, const spi_bus_config_t *c, int dma) {
    assert(host==SPI2_HOST && dma==SPI_DMA_DISABLED);
    assert(c->sclk_io_num==6 && c->mosi_io_num==7 && c->miso_io_num==14);
    return ESP_OK;
}
esp_err_t spi_bus_add_device(int host, const spi_device_interface_config_t *c, spi_device_handle_t *d) {
    assert(host==SPI2_HOST && c->spics_io_num==18 && c->clock_speed_hz==1000000 && c->mode==0);
    *d=&bus; attached=true; return ESP_OK;
}
esp_err_t spi_bus_free(int host) { assert(host==SPI2_HOST && !attached); return ESP_OK; }
esp_err_t spi_bus_remove_device(spi_device_handle_t d) { assert(d==&bus); attached=false; return ESP_OK; }
esp_err_t spi_device_polling_transmit(spi_device_handle_t d, spi_transaction_t *t) {
    assert(d==&bus);
    const uint8_t *tx=t->tx_buffer;
    uint8_t *rx=t->rx_buffer;
    unsigned addr=tx[0]*256u+tx[1];
    if (addr==0x0fe) { assert(t->length==32 && !tx[2] && tx[3]==0xad); unlocked=true; }
    else if (addr==0x120 && !tx[2]) {
        assert(t->length==40 && unlocked && !tx[3] && tx[4]==0x30); timing=true; unlocked=false;
    } else if (addr==0x120) {
        assert(t->length==40 && tx[2]==0x80); rx[3]=0; rx[4]=timing ? 0x30 : 0;
    } else {
        assert(addr==0x21c && t->length==48 && tx[2]==0x80);
        if (fail_read) return ESP_FAIL;
        rx[3]=(uint8_t)(counts>>16); rx[4]=(uint8_t)(counts>>8); rx[5]=(uint8_t)counts;
    }
    return ESP_OK;
}
esp_err_t gpio_set_level(int pin,uint32_t value) { assert(pin==21 && value<=1); return ESP_OK; }
esp_err_t gpio_config(const gpio_config_t *c) { (void)c; return ESP_OK; }

/* These values exercise boundaries only. The installation supplies the real settings. */
static const struct voltage_limits limits = {200000, 250000, 5000, 20, 230000, 5750000};
static const struct starter_config config = {.profile=STARTER_OPEN_STOP,.harness_profile=STARTER_OPEN_STOP,
    .independent_shutdown=true,.contact_settle_ms=5,.start_range={5,20},.start_pulse_ms=10,
    .confirm_stop_ms=150,.max_run_ms=60000};
static struct panel_sample in;
static uint32_t now;
static struct panel_controls panel;
static spi_device_handle_t dev;

static struct panel_result tick(uint32_t dt) {
    struct panel_result result;
    now+=dt;
    in.tank_scanned_at_ms=in.sampled_at_ms=in.protection_checked_at_ms=now;
    esp_err_t code=metered_gpio_step(dev,&panel,now,in,&result);
    assert(code==(fail_read ? ESP_FAIL : !timing ? ESP_ERR_INVALID_RESPONSE : ESP_OK));
    return result;
}

static void run_then_fault(unsigned fault, bool automatic) {
    assert(metered_dol_configure(&panel,config,false,4,20,limits));
    now=UINT32_MAX-20; counts=5750000; fail_read=false; timing=true;
    in=(struct panel_sample){.gpio_a=5,.gpio_b=1|2|4|32|64,.valid=true,.process_healthy=true,
        .motor_stopped=true,.tank_levels_valid=true,.fill_demand=true};
    assert(tick(0).voltage_status==VOLTAGE_RECOVERING);
    for (unsigned k=0;k<310;k++) tick(10);
    if (automatic) {
        in.gpio_b|=8; tick(1); assert(tick(5).mode==PANEL_AUTO); in.gpio_b&=~8;
        for (unsigned k=0;k<310;k++) tick(10);
    }
    in.gpio_b&=~1; tick(1); assert(tick(5).drive.arm_issued);
    tick(5); assert(tick(5).drive.start_issued);
    in.motor_stopped=false;
    if (fault==0) counts=5000000;
    if (fault==1) counts=6250000;
    if (fault==2) fail_read=true;
    if (fault==3) timing=false;
    if (fault==4) counts=0xffffff;
    struct panel_result r=tick(5);
    assert(r.drive.stop_issued && !r.drive.permit_d && !r.drive.run_cmd && !r.auto_enabled);
    assert(r.voltage_status==(fault==0 ? VOLTAGE_LOW : fault==1 ? VOLTAGE_HIGH : VOLTAGE_UNAVAILABLE));
    counts=5750000; fail_read=false; timing=true; in.motor_stopped=true;
    for (unsigned k=0;k<350;k++) {
        r=tick(10); assert(!r.drive.permit_d && !r.drive.arm_issued && !r.auto_enabled);
    }
    assert(r.voltage_status==VOLTAGE_OK && r.mains_mv==230000);
}

int main(void) {
    assert(metered_spi_init(&dev)==ESP_OK && attached);
    assert(!metered_dol_configure(&panel,config,false,4,20,(struct voltage_limits){0}));
    assert(panel.outputs.config.profile==STARTER_DISABLED);
    for (unsigned i=0;i<5;i++) { run_then_fault(i,false); run_then_fault(i,true); }
    struct voltage_window w={0};
    struct voltage_sample s={.counts=5750000,.acquired_ms=4,.valid=true};
    assert(voltage_update(&w,limits,s,4,20)==VOLTAGE_RECOVERING);
    assert(voltage_update(&w,limits,s,24,20)==VOLTAGE_RECOVERING);
    assert(voltage_update(&w,limits,s,25,20)==VOLTAGE_UNAVAILABLE);
    s.acquired_ms=30; voltage_update(&w,limits,s,30,20);
    s.acquired_ms=50; assert(voltage_update(&w,limits,s,50,20)==VOLTAGE_OK);
    s.counts=5000000; s.acquired_ms=51; assert(voltage_update(&w,limits,s,51,20)==VOLTAGE_LOW);
    s.counts=5062500; s.acquired_ms=52; assert(voltage_update(&w,limits,s,52,20)==VOLTAGE_RECOVERING);
    s.counts=5750000; s.acquired_ms=72; assert(voltage_update(&w,limits,s,72,20)==VOLTAGE_RECOVERING);
    s.acquired_ms=92; assert(voltage_update(&w,limits,s,92,20)==VOLTAGE_OK);
    s.acquired_ms=91; assert(voltage_update(&w,limits,s,93,20)==VOLTAGE_UNAVAILABLE);
    return 0;
}
