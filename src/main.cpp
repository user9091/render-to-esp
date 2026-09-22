#include <Arduino.h>
#include <ESPmDNS.h>
#include <WebServer.h>
#include <WiFi.h>
#include <SPI.h>
#include <GxEPD2_BW.h>
#include "config.h"

constexpr size_t PANEL_WIDTH = EPD_DRIVER::WIDTH;
constexpr size_t PANEL_HEIGHT = EPD_DRIVER::HEIGHT;
static_assert(PANEL_WIDTH == 400 && PANEL_HEIGHT == 300, "Check the selected panel driver");
constexpr size_t IMAGE_WIDTH = PANEL_HEIGHT;
constexpr size_t IMAGE_HEIGHT = PANEL_WIDTH;
constexpr size_t IMAGE_BYTES = ((IMAGE_WIDTH + 7) / 8) * IMAGE_HEIGHT;
static uint8_t bitmap[IMAGE_BYTES];
static size_t received = 0;
static bool uploadAccepted = false;
static bool uploadFailed = false;

GxEPD2_BW<EPD_DRIVER, 16> display(EPD_DRIVER(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY));
WebServer server(80);

static bool authorized() {
  return server.hasHeader("X-Image-Token") &&
         server.header("X-Image-Token") == IMAGE_TOKEN;
}

static void showBitmap() {
  display.setRotation(1);
  display.setFullWindow();
  display.firstPage();
  do {
    display.fillScreen(GxEPD_WHITE);
    display.drawBitmap(0, 0, bitmap, IMAGE_WIDTH, IMAGE_HEIGHT, GxEPD_BLACK);
  } while (display.nextPage());
  display.hibernate();
}

static void onImageUpload() {
  HTTPUpload& upload = server.upload();
  if (upload.status == UPLOAD_FILE_START) {
    received = 0;
    uploadFailed = false;
    uploadAccepted = authorized();
  } else if (upload.status == UPLOAD_FILE_WRITE && uploadAccepted && !uploadFailed) {
    if (received + upload.currentSize <= IMAGE_BYTES) {
      memcpy(bitmap + received, upload.buf, upload.currentSize);
      received += upload.currentSize;
    } else {
      uploadFailed = true;
    }
  } else if (upload.status == UPLOAD_FILE_ABORTED) {
    uploadFailed = true;
  }
}

static void onImageComplete() {
  if (!authorized()) {
    server.send(401, "text/plain", "Invalid image token");
  } else if (!uploadAccepted || uploadFailed || received != IMAGE_BYTES) {
    server.send(400, "text/plain", "Expected 15200 raw bitmap bytes");
  } else {
    server.send(200, "text/plain", "Image received; updating display");
    showBitmap();
    Serial.println("Display updated");
  }
}

void setup() {
  Serial.begin(115200);
  SPI.begin(EPD_SCK, -1, EPD_MOSI, EPD_CS);
  display.init(115200);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print('.');
  }
  Serial.print("ESP address: http://");
  Serial.println(WiFi.localIP());
  if (MDNS.begin("render-to-esp")) {
    MDNS.addService("http", "tcp", 80);
    Serial.println("mDNS: render-to-esp.local");
  }
  const char* headers[] = {"X-Image-Token"};
  server.collectHeaders(headers, 1);
  server.on("/image", HTTP_POST, onImageComplete, onImageUpload);
  server.on("/health", HTTP_GET, []() { server.send(200, "text/plain", "ready"); });
  server.begin();
}

void loop() {
  server.handleClient();
}
