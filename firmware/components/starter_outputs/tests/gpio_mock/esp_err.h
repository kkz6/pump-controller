/* Host GPIO fault-injection fixture. */
#ifndef TEST_ESP_ERR_H
#define TEST_ESP_ERR_H
typedef int esp_err_t;
enum { ESP_OK=0, ESP_FAIL=-1, ESP_ERR_INVALID_ARG=1, ESP_ERR_INVALID_STATE=2, ESP_ERR_INVALID_RESPONSE=3 };
#endif
