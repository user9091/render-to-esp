#pragma once

// Copy to config.h and fill these in. config.h is ignored by Git.
#define WIFI_SSID "your-wifi-name"
#define WIFI_PASSWORD "your-wifi-password"
#define IMAGE_TOKEN "choose-a-long-random-token"

// GPIO numbers, not physical pin numbers. Change to match your wiring.
#define EPD_SCK 6
#define EPD_MOSI 7
#define EPD_CS 10
#define EPD_DC 9
#define EPD_RST 4
#define EPD_BUSY 5

// WeAct Studio 4.2-inch black/white module: 400x300, SSD1683.
#define EPD_DRIVER GxEPD2_420_GDEY042T81
