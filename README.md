# Render to ESP

Right-click an image in GNOME Files on Fedora, choose **Render to ESP**, and show it on a Wi-Fi-connected ESP32-C3 e-paper display.

The sender fits the image to **300 × 400 portrait**, preserves its proportions, places it on white, darkens midtones, and converts it to black and white with dithering. The ESP receives a one-bit bitmap and refreshes the display. Your original image is not changed.

This project was built and tested on **Fedora 44**, an **ESP32-C3**, and the **WeAct Studio 4.2-inch black-and-white SPI e-paper module**. WeAct's [example identifies this panel](https://github.com/WeActStudio/WeActStudio.EpaperModule/blob/master/Example/EpaperModuleTest_Arduino_ESP32/EpaperModuleTest_Arduino_ESP32.ino) as 400 × 300 using `GxEPD2_420_GDEY042T81`. The firmware rotates that physical panel to show 300 × 400 images.

## 1. Install Fedora packages

```sh
sudo dnf install git platformio python3-pillow nautilus-python
```

Clone or download this repository and open a terminal in its directory. GNOME Files (Nautilus) is required for the right-click menu. The command-line sender works without Nautilus.

## 2. Wire the display

Connect the display module to the ESP32-C3 using these **GPIO numbers**. They are not physical header positions. Set `EPD_SCK` and `EPD_MOSI` in the config file if your wiring uses different pins.

| WeAct display pin | ESP32-C3 GPIO |
| --- | ---: |
| CLK / SCK | 6 |
| DIN / MOSI | 7 |
| CS | 10 |
| DC | 9 |
| RST / RES | 4 |
| BUSY | 5 |

Connect VCC and GND according to your module's markings. This project targets the black-and-white module; a color or different-size panel needs a matching GxEPD2 driver and image format.

## 3. Set Wi-Fi and flash 

```sh
cp include/config.example.h include/config.h
```

Edit `include/config.h`:

- Set `WIFI_SSID` and `WIFI_PASSWORD` for a **2.4 GHz** Wi-Fi network.
- Replace `IMAGE_TOKEN` with a random string. Generate one with `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'`.
- Check that the GPIO definitions match your wiring.

Connect the ESP32-C3 by USB, then flash it:

```sh
pio run -t upload
```

If PlatformIO cannot find the board, run `pio device list` and use its port, for example `pio run -t upload --upload-port /dev/ttyACM0`. The project enables USB serial logging for ESP32-C3 boards with native USB. `pio device monitor -b 115200` can show the ESP's IP address after it connects.

## 4. Configure the sender 

```sh
cp sender/config.example.json sender/config.json
```

Edit `sender/config.json`. Set `token` to **exactly** the `IMAGE_TOKEN` in `include/config.h`. The default URL is `http://render-to-esp.local/image`. If that name does not resolve on your network, replace it with the ESP's IP address, such as `http://192.168.1.42/image`.

Test the connection and send an image from a terminal:

```sh
curl http://render-to-esp.local/health
python3 sender/send.py /path/to/photo.jpg
```

The health endpoint should return `ready`. If you changed the sender URL to an IP address, use that IP for the health check too. The HTTP response confirms receipt; e-paper refresh may take a few more seconds.

## 5. Add the right-click menu (about 1 minute)

```sh
bash nautilus/install.sh
```

Reopen GNOME Files. Right-click **one local image** and choose **Render to ESP**. A desktop notification reports success or failure. The installer links the extension to this checkout, so keep the repository at the same path. On Fedora, the extension needs the `nautilus-python` package from step 1.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `pio run -t upload` cannot find a port | Run `pio device list` and supply `--upload-port`. Check the USB cable supports data. |
| ESP never appears on Wi-Fi | Check the SSID and password in `include/config.h`, use 2.4 GHz Wi-Fi, and flash again. |
| `render-to-esp.local` does not resolve | Use the ESP's printed IP address in `sender/config.json`. |
| `Invalid image token` | Make `sender/config.json` and `include/config.h` tokens identical, then flash again. |
| No right-click item | Confirm `nautilus-python` is installed, run `bash nautilus/install.sh`, and reopen GNOME Files. |

## How it works and privacy

The Python sender uses Pillow to apply EXIF rotation, fit the image, darken midtones, and dither to one-bit black and white. It packs each 300-pixel row into 38 bytes, including two padding bits, for a **15,200-byte** upload. The ESP checks the token, draws the bitmap at rotation 1, and performs a full e-paper refresh.

`include/config.h`, `sender/config.json`, and `.pio/` are ignored by Git. Do not commit Wi-Fi credentials or tokens. The transfer uses ordinary HTTP on the local network, so use this on a network you trust.

To use another panel, change the GxEPD2 driver, wiring, image dimensions, and row-byte calculation together. A different 4.2-inch panel may use a different controller even when its resolution matches.
