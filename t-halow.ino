#include "utilities.h"
#include <SPI.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include "FS.h"
#include "SD.h"
#include "SPI.h"
#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

#define BUF_MAX_LEN 20
#define CONFIG_FILE "/config.json"

#define AH_Rx00P_RESPONE_OK 1
#define AH_Rx00P_RESPONE_ERROR 2

bool ssd1306_ret = false;
bool camera_ret = false;
bool sdcard_ret = false;
bool tx_ah_ret = false;
char buf[BUF_MAX_LEN] = {0};

camera_config_t config;
Adafruit_SSD1306 display = Adafruit_SSD1306(128, 64, &Wire);
SemaphoreHandle_t debuglock;

WebServer server(80);

struct Config {
    String mode;
    int bss_bw;
    String freq_range;
    String key_mgmt;
    String wpa_psk;
    String ssid;
    int txpower;
    String r_ssid;
    String r_psk;
    bool super_pwr;
    String wifi_ssid;
    String wifi_pass;
} deviceConfig;

bool loadConfig() {
    File configFile = SD.open(CONFIG_FILE, "r");
    if (!configFile) {
        Serial.println("Failed to open config file");
        return false;
    }

    size_t size = configFile.size();
    std::unique_ptr<char[]> buf(new char[size]);
    configFile.readBytes(buf.get(), size);

    DynamicJsonDocument json(1024);
    auto deserializeError = deserializeJson(json, buf.get());
    if (deserializeError) {
        Serial.println("Failed to parse config file");
        return false;
    }

    deviceConfig.mode = json["mode"].as<String>();
    deviceConfig.bss_bw = json["bss_bw"];
    deviceConfig.freq_range = json["freq_range"].as<String>();
    deviceConfig.key_mgmt = json["key_mgmt"].as<String>();
    deviceConfig.wpa_psk = json["wpa_psk"].as<String>();
    deviceConfig.ssid = json["ssid"].as<String>();
    deviceConfig.txpower = json["txpower"];
    deviceConfig.r_ssid = json["r_ssid"].as<String>();
    deviceConfig.r_psk = json["r_psk"].as<String>();
    deviceConfig.super_pwr = json["super_pwr"];
    deviceConfig.wifi_ssid = json["wifi_ssid"].as<String>();
    deviceConfig.wifi_pass = json["wifi_pass"].as<String>();

    configFile.close();
    return true;
}

void sendATCommand(const String& command, const String& value) {
    if (!value.isEmpty()) {
        sendAT(command + "=" + value);
        waitResponse();
    }
}

void applyConfig() {
    sendATCommand("+MODE", deviceConfig.mode);
    sendATCommand("+BSS_BW", String(deviceConfig.bss_bw));
    sendATCommand("+FREQ_RANGE", deviceConfig.freq_range);
    sendATCommand("+KEY_MGMT", deviceConfig.key_mgmt);
    if (deviceConfig.key_mgmt == "WPA-PSK") {
        sendATCommand("+WPA_PSK", deviceConfig.wpa_psk);
    }
    sendATCommand("+SSID", deviceConfig.ssid);
    sendATCommand("+TXPOWER", String(deviceConfig.txpower));
    sendATCommand("+R_SSID", deviceConfig.r_ssid);
    sendATCommand("+R_PSK", deviceConfig.r_psk);
    sendATCommand("+SUPER_PWR", String(deviceConfig.super_pwr));
}

void handleRoot() {
    server.send(200, "text/html", "<html><body><h1>T-Halow Tools</h1><p>Use the tabs to configure and debug the device.</p></body></html>");
}

void handleSettings() {
    String settingsPage = "<html><body><h1>Halow Settings</h1>";
    settingsPage += "<p>Mode: " + deviceConfig.mode + "</p>";
    settingsPage += "<p>BSS BW: " + String(deviceConfig.bss_bw) + " MHz</p>";
    settingsPage += "<p>Frequency Range: " + deviceConfig.freq_range + "</p>";
    settingsPage += "<p>Key Management: " + deviceConfig.key_mgmt + "</p>";
    if (deviceConfig.key_mgmt == "WPA-PSK") {
        settingsPage += "<p>WPA PSK: " + deviceConfig.wpa_psk + "</p>";
    }
    settingsPage += "<p>SSID: " + deviceConfig.ssid + "</p>";
    settingsPage += "<p>Transmit Power: " + String(deviceConfig.txpower) + "</p>";
    settingsPage += "<p>Remote SSID: " + deviceConfig.r_ssid + "</p>";
    settingsPage += "<p>Remote PSK: " + deviceConfig.r_psk + "</p>";
    settingsPage += "<p>Super Power: " + String(deviceConfig.super_pwr) + "</p>";
    settingsPage += "</body></html>";

    server.send(200, "text/html", settingsPage);
}

void handleSendAT() {
    if (server.hasArg("command")) {
        String command = server.arg("command");
        sendAT(command);
        server.send(200, "text/plain", "Command sent: " + command);
    } else {
        server.send(400, "text/plain", "Command parameter missing");
    }
}

void setupWebServer() {
    server.on("/", handleRoot);
    server.on("/settings", handleSettings);
    server.on("/sendAT", handleSendAT);

    server.begin();
    Serial.println("HTTP server started");
}

// Existing functions...

void setup() {
    Serial.begin(115200);
    delay(3000);

    debuglock = xSemaphoreCreateBinary();
    assert(debuglock);
    xSemaphoreGive(debuglock);

    Wire.begin(BOARD_I2C_SDA, BOARD_I2C_SCL);
    SPI.begin(TF_SPI_SCK, TF_SPI_MISO, TF_SPI_MOSI, TF_SPI_CS);
    SerialAT.begin(115200, SERIAL_8N1, SERIAL_AT_RXD, SERIAL_AT_TXD);

    ssd1306_ret = ssd1306_init();
    camera_ret = camera_init();
    sdcard_ret = sdcard_init();
    tx_ah_ret = TX_AH_init();

    if (!loadConfig()) {
        Serial.println("Failed to load configuration");
    } else {
        applyConfig();
    }

    // Setup WiFi
    const char* ssid = deviceConfig.wifi_ssid.isEmpty() ? "t-halow" : deviceConfig.wifi_ssid.c_str();
    const char* password = deviceConfig.wifi_pass.isEmpty() ? "12345678" : deviceConfig.wifi_pass.c_str();
    WiFi.softAP(ssid, password);
    setupWebServer();

    lcd_info_show();
}

uint32_t last_tick = 0;
uint32_t rssi_tick = 0;

void loop() {
    server.handleClient();

    if (millis() - last_tick > 5000) {
        last_tick = millis();
        // Update status or other periodic tasks
    }

    if (millis() - rssi_tick > 3000) {
        rssi_tick = millis();

        String data;
        sendAT("+CONN_STATE");
        if (waitResponse(1000, data, "+CONNECTED", "+DISCONNECT") == AH_Rx00P_RESPONE_OK) {
            tx_ah_conn_status = true;
        } else {
            tx_ah_conn_status = false;
        }

        if (tx_ah_conn_status) {
            String rssi_data;
            sendAT("+RSSI=1");
            if (waitResponse(1000, rssi_data) == AH_Rx00P_RESPONE_OK) {
                int startIndex = rssi_data.indexOf(':');
                int endIndex = rssi_data.lastIndexOf('\n');
                String substr = rssi_data.substring(startIndex + 1, endIndex);
                strcpy(rssi_buf, substr.c_str());
            }

            String send_data = "11111100000000";
            String data = String(send_indx);
            int len = send_data.length() + data.length();
            String cmd = "+TXDATA=" + String(len);

            send_data = send_data + data;
            Serial.printf("len=%d, send_data=%s, cmd=%s\n", len, send_data.c_str(), cmd.c_str());

            sendAT(cmd);
            if (waitResponse() == AH_Rx00P_RESPONE_OK) {
                SerialAT.write(send_data.c_str());
            }

            send_indx++;
        }

        lcd_info_show();
    }

    while (SerialAT.available()) {
        SerialMon.write(SerialAT.read());
    }
    while (SerialMon.available()) {
        SerialAT.write(SerialMon.read());
    }
    delay(1);
}
