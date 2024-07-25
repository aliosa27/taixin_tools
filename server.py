from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from werkzeug.utils import secure_filename
import subprocess
import re
import os
import json
import time

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp/'
ALLOWED_EXTENSIONS = {'bin'}

# Define the list of set and get commands
SET_COMMANDS = [
    'country_region', 'ssid', 'channel', 'rts_threshold', 'frag_threshold', 'key_mgmt', 'wpa_psk',
    'bssid_filter', 'freq_range', 'bss_bw', 'tx_bw', 'tx_mcs', 'acs', 'bgrssi', 'chan_list', 'mode', 'paired_stas',
    'pairing', 'beacon_int', 'radio_onoff', 'join_group', 'ether_type', 'txpower', 'agg_cnt', 'ps_connect',
    'bss_max_idle', 'wkio_mode', 'loaddef', 'disassoc_sta', 'dtim_period', 'ps_mode', 'aplost_time', 'unpair',
    'auto_chswitch', 'mcast_key', 'reassoc_wkhost', 'wakeup_io', 'dbginfo', 'sysdbg', 'primary_chan', 'autosleep_time',
    'super_pwr', 'r_ssid', 'r_psk', 'auto_save', 'pair_autostop', 'dcdc13', 'acktmo', 'pa_pwrctl_dis', 'dhcpc',
    'wkdata_save', 'mcast_txparam', 'reset_sta', 'ant_auto', 'ant_sel', 'wkhost_reason', 'macfilter', 'atcmd', 'roaming',
    'ap_hide', 'max_txcnt', 'assert_holdup', 'ap_psmode', 'dupfilter', 'dis_1v1m2u', 'dis_psconnect', 'reset',
    'heartbeat', 'heartbeat_resp', 'wakeup_data', 'wakeup', 'custmgmt', 'mgmtframe', 'wkdata_mask', 'driverdata',
    'freqinfo', 'blenc', 'sleep', 'hwscan', 'user_edca', 'fix_txrate', 'nav_max', 'clr_nav', 'cca_param', 'tx_modgain',
    'rts_duration', 'disable_print', 'conn_paironly', 'diffcust_conn', 'wait_psmode', 'standby', 'ap_chansw', 'cca_ce',
    'rtc', 'apep_padding', 'watchdog', 'retry_fallback_cnt', 'fallback_mcs', 'xosc', 'freq_cali_period', 'cust_drvdata',
    'max_txdelay', 'heartbeat_int', 'atcmd'
]

GET_COMMANDS = [
    'mode', 'sta_list', 'scan_list', 'ssid', 'bssid', 'wpa_psk', 'txpower', 'agg_cnt', 'bss_bw', 'chan_list', 'freq_range',
    'key_mgmt', 'battery_level', 'module_type', 'disassoc_reason', 'ant_sel', 'wkreason', 'wkdata_buff', 'temperature',
    'conn_state', 'sta_count', 'txq_param', 'nav', 'rtc', 'bgrssi', 'center_freq', 'acs_result', 'reason_code', 'status_code',
    'dhcpc_result', 'xosc', 'freq_offset', 'fwinfo', 'stainfo', 'signal'
]

CONFIG_DIR = '/etc/'
LAST_SETTINGS_FILE = os.path.join(CONFIG_DIR, 'last_settings.json')
CURRENT_SETTINGS_FILE = os.path.join(CONFIG_DIR, 'hgicf.conf')
BACKUP_SETTINGS_FILE = os.path.join(CONFIG_DIR, 'hgicf-backup.conf')
DEFAULT_SETTINGS_FILE = os.path.join(CONFIG_DIR, 'hgicf-template.conf')
WIFI_SSID_FILE = '/boot/wifi.ssid'
WIFI_PASS_FILE = '/boot/wifi.pass'

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Taixin Tool</title>
    <link rel="stylesheet" href="/static/bootstrap.min.css">
    <script src="/static/chart.min.js"></script>
    <script src="/static/moment.min.js"></script>
    <script src="/static/chartjs-adapter-moment.min.js"></script>
    <style>
        body {
            padding-top: 50px;
        }
        .container {
            max-width: 700px;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        .nav-tabs {
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center">Taixin Tool</h1>
        <ul class="nav nav-tabs">
            <li class="nav-item">
                <a class="nav-link active" href="#home" data-toggle="tab">Home</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="#station-settings" data-toggle="tab">Station Settings</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="#quick-pair" data-toggle="tab">Quick Pair</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="#network-settings" data-toggle="tab">Network Settings</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="#system" data-toggle="tab">System</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="#wifi-settings" data-toggle="tab">WiFi Settings</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" href="#site-survey" data-toggle="tab">Site Survey</a>
            </li>
        </ul>
        <div class="tab-content">
            <div class="tab-pane fade show active" id="home">
                <h2>Current Settings</h2>
                <p><strong>SSID:</strong> {{ current_settings['ssid'] }}</p>
                <p><strong>BSSID:</strong> {{ current_settings['bssid'] }}</p>
                <p><strong>Tx Power:</strong> {{ current_settings['txpower'] }}</p>
                <p><strong>BSS BW:</strong> {{ current_settings['bss_bw'] }}</p>
                <p><strong>Connection State:</strong> <span id="conn_state">{{ current_settings['conn_state'] }}</span></p>
                <form id="commandForm">
                    <div class="form-group">
                        <label for="commandType">Select Command Type:</label>
                        <select class="form-control" id="commandType" name="commandType" onchange="updateCommands()">
                            <option value="get">Get</option>
                            <option value="set">Set</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="command">Select Command:</label>
                        <select class="form-control" id="command" name="command" onchange="checkSignal()"></select>
                    </div>
                    <div class="form-group" id="valueGroup">
                        <label for="value">Value (for Set commands only):</label>
                        <input type="text" class="form-control" id="value" name="value">
                    </div>
                    <div class="form-group" id="intervalGroup" style="display: none;">
                        <label for="interval">Refresh Interval (seconds):</label>
                        <input type="number" class="form-control" id="interval" name="interval" value="5" min="1">
                    </div>
                    <button type="button" class="btn btn-primary" onclick="sendCommand()">Send</button>
                </form>
                <h2>Response:</h2>
                <pre id="response" class="bg-light p-3 border rounded"></pre>
                <canvas id="signalChart" width="400" height="200"></canvas>
            </div>
            <div class="tab-pane fade" id="station-settings">
                <h2>Station Settings</h2>
                <form id="stationSettingsForm">
                    <div class="form-group">
                        <label for="ssid">SSID:</label>
                        <input type="text" class="form-control" id="ssid" name="ssid">
                    </div>
                    <div class="form-group">
                        <label for="super_pwr">Super Power:</label>
                        <input type="text" class="form-control" id="super_pwr" name="super_pwr">
                    </div>
                    <div class="form-group">
                        <label for="wpa_psk">WPA PSK:</label>
                        <input type="text" class="form-control" id="wpa_psk" name="wpa_psk">
                    </div>
                    <div class="form-group">
                        <label for="key_mgmt">Key Management:</label>
                        <select class="form-control" id="key_mgmt" name="key_mgmt" onchange="validateKeyMgmt()">
                            <option value="WPA-PSK">WPA-PSK</option>
                            <option value="NONE">NONE</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="tx_mcs">Tx MCS:</label>
                        <input type="text" class="form-control" id="tx_mcs" name="tx_mcs">
                    </div>
                    <div class="form-group">
                        <label for="freq_range">Frequency Range:</label>
                        <input type="text" class="form-control" id="freq_range" name="freq_range">
                    </div>
                    <div class="form-group">
                        <label for="bss_bw">BSS BW:</label>
                        <select class="form-control" id="bss_bw" name="bss_bw">
                            <option value="1">1 MHz</option>
                            <option value="2">2 MHz</option>
                            <option value="4">4 MHz</option>
                            <option value="8">8 MHz</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="mode">Mode:</label>
                        <select class="form-control" id="mode" name="mode" onchange="toggleApStaFields()">
                            <option value="ap">Access Point</option>
                            <option value="sta">Station</option>
                            <option value="group">Broadcast</option>
                            <option value="apsta">Access Point/Station</option>
                        </select>
                    </div>
                    <div class="form-group" id="r_ssid_group" style="display: none;">
                        <label for="r_ssid">Remote SSID:</label>
                        <input type="text" class="form-control" id="r_ssid" name="r_ssid">
                    </div>
                    <div class="form-group" id="r_psk_group" style="display: none;">
                        <label for="r_psk">Remote PSK:</label>
                        <input type="text" class="form-control" id="r_psk" name="r_psk">
                    </div>
                    <button type="button" class="btn btn-primary" onclick="saveStationSettings()">Save Settings</button>
                    <button type="button" class="btn btn-warning" onclick="restoreDefaults()">Restore Defaults</button>
                </form>
            </div>
            <div class="tab-pane fade" id="quick-pair">
                <h2>Quick Pair</h2>
                <button type="button" class="btn btn-primary" onclick="quickPair()">Start Pairing</button>
                <h3>Pairing Details</h3>
                <pre id="pairingDetails" class="bg-light p-3 border rounded"></pre>
            </div>
            <div class="tab-pane fade" id="network-settings">
                <h2>Network Settings</h2>
                <form id="networkSettingsForm">
                    <div class="form-group">
                        <label for="ip_address">IP Address:</label>
                        <input type="text" class="form-control" id="ip_address" name="ip_address">
                    </div>
                    <div class="form-group">
                        <label for="netmask">Netmask:</label>
                        <input type="text" class="form-control" id="netmask" name="netmask">
                    </div>
                    <div class="form-group">
                        <label for="gateway">Gateway:</label>
                        <input type="text" class="form-control" id="gateway" name="gateway">
                    </div>
                    <button type="button" class="btn btn-primary" onclick="saveNetworkSettings()">Save Network Settings</button>
                </form>
                <h2>Current Network Settings</h2>
                <p><strong>IP Address:</strong> <span id="current_ip_address">{{ current_network_settings['ip_address'] }}</span></p>
                <p><strong>Netmask:</strong> <span id="current_netmask">{{ current_network_settings['netmask'] }}</span></p>
                <p><strong>Gateway:</strong> <span id="current_gateway">{{ current_network_settings['gateway'] }}</span></p>
            </div>
            <div class="tab-pane fade" id="system">
                <h2>System</h2>
                <button type="button" class="btn btn-danger" onclick="rebootSystem()">Reboot</button>
                <h3>Run Command</h3>
                <form id="systemCommandForm">
                    <div class="form-group">
                        <label for="syscommand">Command:</label>
                        <input type="text" class="form-control" id="syscommand" name="syscommand">
                    </div>
                    <button type="button" class="btn btn-primary" onclick="runSystemCommand()">Run</button>
                </form>
                <h3>Command Output:</h3>
                <pre id="commandOutput" class="bg-light p-3 border rounded"></pre>
                <h3>Firmware Upload</h3>
                <form action="/upload_firmware" method="post" enctype="multipart/form-data">
                    <div class="form-group">
                        <label for="firmware">Choose firmware file:</label>
                        <input type="file" class="form-control" id="firmware" name="firmware">
                    </div>
                    <button type="submit" class="btn btn-primary">Upload</button>
                </form>
            </div>
            <div class="tab-pane fade" id="wifi-settings">
                <h2>WiFi Settings</h2>
                <form id="wifiSettingsForm">
                    <div class="form-group">
                        <label for="wifi_ssid">SSID:</label>
                        <input type="text" class="form-control" id="wifi_ssid" name="wifi_ssid">
                    </div>
                    <div class="form-group">
                        <label for="wifi_pass">Password:</label>
                        <input type="text" class="form-control" id="wifi_pass" name="wifi_pass">
                    </div>
                    <button type="button" class="btn btn-primary" onclick="saveWiFiSettings()">Save WiFi Settings</button>
                </form>
            </div>
            <div class="tab-pane fade" id="site-survey">
                <h2>Site Survey</h2>
                <button type="button" class="btn btn-primary" onclick="runSiteSurvey()">Run Site Survey</button>
                <h3>Survey Results</h3>
                <table class="table table-bordered">
                    <thead>
                        <tr>
                            <th>BSSID</th>
                            <th>SSID</th>
                            <th>Encryption</th>
                            <th>Frequency</th>
                            <th>Signal</th>
                        </tr>
                    </thead>
                    <tbody id="surveyResults">
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    <script>
        const setCommands = {{ set_commands | tojson }};
        const getCommands = {{ get_commands | tojson }};
        let rssiInterval;
        let signalChart;
        let signalData = [];
        let connStateInterval;

        function updateCommands() {
            const commandType = document.getElementById('commandType').value;
            const commandSelect = document.getElementById('command');
            commandSelect.innerHTML = '';
            const commands = commandType === 'get' ? getCommands : setCommands;
            commands.forEach(cmd => {
                const option = document.createElement('option');
                option.value = cmd;
                option.textContent = cmd;
                commandSelect.appendChild(option);
            });
            document.getElementById('valueGroup').style.display = commandType === 'set' ? 'block' : 'none';
        }

        function checkSignal() {
            const command = document.getElementById('command').value;
            const intervalGroup = document.getElementById('intervalGroup');
            if (command === 'signal') {
                intervalGroup.style.display = 'block';
                setupChart();
            } else {
                intervalGroup.style.display = 'none';
                clearInterval(rssiInterval);
                if (signalChart) {
                    signalChart.destroy();
                    signalChart = null;
                }
            }
        }

        function sendCommand() {
            const commandType = document.getElementById('commandType').value;
            const command = document.getElementById('command').value;
            const value = document.getElementById('value').value;
            const interval = document.getElementById('interval').value;
            const url = `/command?cmd=${commandType}&param=${encodeURIComponent(command)}${commandType === 'set' ? '&value=' + encodeURIComponent(value) : ''}`;
            
            if (command === 'signal') {
                clearInterval(rssiInterval);
                fetchAndUpdateSignal(url);
                rssiInterval = setInterval(() => fetchAndUpdateSignal(url), interval * 1000);
            } else {
                fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        const responseText = data.response.replace(/^RESP:\\d+\\s*/, '');
                        document.getElementById('response').innerText = responseText;
                    });
            }
        }

        function fetchAndUpdateSignal(url) {
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    const responseText = data.response.replace(/^RESP:\\d+\\s*/, '');
                    document.getElementById('response').innerText = responseText;
                    const matches = responseText.match(/-?\\d+/);
                    if (matches) {
                        const rssi = parseInt(matches[0]);
                        const now = new Date();
                        signalData.push({x: now, y: rssi});
                        if (signalData.length > 20) {
                            signalData.shift();
                        }
                        if (signalChart) {
                            signalChart.update();
                        }
                    }
                });
        }

        function setupChart() {
            const ctx = document.getElementById('signalChart').getContext('2d');
            signalChart = new Chart(ctx, {
                type: 'line',
                data: {
                    datasets: [{
                        label: 'Signal',
                        data: signalData,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    }]
                },
                options: {
                    scales: {
                        x: {
                            type: 'time',
                            time: {
                                unit: 'second'
                            }
                        },
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        function validateKeyMgmt() {
            const keyMgmt = document.getElementById('key_mgmt').value;
            const wpaPskInput = document.getElementById('wpa_psk');
            if (keyMgmt === 'WPA-PSK') {
                wpaPskInput.setAttribute('maxlength', '64');
            } else {
                wpaPskInput.removeAttribute('maxlength');
            }
        }

        function toggleApStaFields() {
            const mode = document.getElementById('mode').value;
            const rSsidGroup = document.getElementById('r_ssid_group');
            const rPskGroup = document.getElementById('r_psk_group');
            if (mode === 'apsta') {
                rSsidGroup.style.display = 'block';
                rPskGroup.style.display = 'block';
            } else {
                rSsidGroup.style.display = 'none';
                rPskGroup.style.display = 'none';
            }
        }

        function loadStationSettings() {
            fetch('/load_station_settings')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        document.getElementById('ssid').value = data.settings.ssid || '';
                        document.getElementById('super_pwr').value = data.settings.super_pwr || '';
                        document.getElementById('wpa_psk').value = data.settings.wpa_psk || '';
                        document.getElementById('key_mgmt').value = data.settings.key_mgmt || 'NONE';
                        document.getElementById('tx_mcs').value = data.settings.tx_mcs || '';
                        document.getElementById('freq_range').value = data.settings.freq_range || '';
                        document.getElementById('bss_bw').value = data.settings.bss_bw || '1';
                        document.getElementById('mode').value = data.settings.mode || 'ap';
                        document.getElementById('r_ssid').value = data.settings.r_ssid || '';
                        document.getElementById('r_psk').value = data.settings.r_psk || '';
                        toggleApStaFields();
                    }
                });
        }

        function saveStationSettings() {
            const settings = {
                ssid: document.getElementById('ssid').value,
                super_pwr: document.getElementById('super_pwr').value,
                wpa_psk: document.getElementById('wpa_psk').value,
                key_mgmt: document.getElementById('key_mgmt').value,
                tx_mcs: document.getElementById('tx_mcs').value,
                freq_range: document.getElementById('freq_range').value,
                bss_bw: document.getElementById('bss_bw').value,
                mode: document.getElementById('mode').value,
                r_ssid: document.getElementById('r_ssid').value,
                r_psk: document.getElementById('r_psk').value
            };
            if (settings.key_mgmt === 'WPA-PSK' && settings.wpa_psk.length !== 64) {
                alert('WPA PSK must be exactly 64 characters long.');
                return;
            }
            if (settings.mode === 'apsta' && (!settings.r_ssid || (settings.r_psk && settings.r_psk.length !== 64))) {
                alert('Remote SSID must be set for AP/STA mode, and Remote PSK must be 64 characters long if set.');
                return;
            }
            fetch('/station_settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            }).then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    if (confirm('Settings saved successfully. Would you like to reboot now?')) {
                        rebootSystem();
                    } else {
                        alert('Settings saved successfully.');
                    }
                } else {
                    alert('Failed to save settings.');
                }
            });
        }

        function restoreDefaults() {
            fetch('/restore_defaults', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        alert('Defaults restored successfully. Please save the settings to apply.');
                    } else {
                        alert('Failed to restore defaults.');
                    }
                });
        }

        function saveNetworkSettings() {
            const settings = {
                ip_address: document.getElementById('ip_address').value,
                netmask: document.getElementById('netmask').value,
                gateway: document.getElementById('gateway').value
            };
            fetch('/network_settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            }).then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    alert('Network settings saved successfully.');
                    document.getElementById('current_ip_address').innerText = settings.ip_address;
                    document.getElementById('current_netmask').innerText = settings.netmask;
                    document.getElementById('current_gateway').innerText = settings.gateway;
                } else {
                    alert('Failed to save network settings.');
                }
            });
        }

        function quickPair() {
            fetch('/quick_pair', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        fetch('/command?cmd=get&param=ssid')
                            .then(response => response.json())
                            .then(ssidData => {
                                const ssid = ssidData.response.replace(/^RESP:\\d+\\s*/, '').trim();
                                fetch('/command?cmd=get&param=wpa_psk')
                                    .then(response => response.json())
                                    .then(wpaPskData => {
                                        const wpa_psk = wpaPskData.response.replace(/^RESP:\\d+\\s*/, '').trim();
                                        document.getElementById('pairingDetails').innerText = `SSID: ${ssid}\\nWPA PSK: ${wpa_psk}`;
                                    });
                            });
                    } else {
                        alert('Failed to start pairing.');
                    }
                });
        }

        function rebootSystem() {
            fetch('/reboot', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        alert('System is rebooting.');
                    } else {
                        alert('Failed to reboot system.');
                    }
                });
        }

        function runSystemCommand() {
            const syscommand = document.getElementById('syscommand').value;
            fetch('/run_command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ command: syscommand })
            }).then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    document.getElementById('commandOutput').innerText = data.output;
                } else {
                    document.getElementById('commandOutput').innerText = 'Failed to run command.';
                }
            });
        }

        function updateConnState() {
            fetch('/command?cmd=get&param=conn_state')
                .then(response => response.json())
                .then(data => {
                    const connState = parseInt(data.response.replace(/^RESP:\\d+\\s*/, '').trim());
                    const connStateElement = document.getElementById('conn_state');
                    switch (connState) {
                        case 0:
                            connStateElement.textContent = 'DISCONNECTED';
                            connStateElement.style.color = 'red';
                            break;
                        case 1:
                            connStateElement.textContent = 'DISABLED';
                            connStateElement.style.color = 'red';
                            break;
                        case 2:
                            connStateElement.textContent = 'INACTIVE';
                            connStateElement.style.color = 'red';
                            break;
                        case 3:
                            connStateElement.textContent = 'SCANNING';
                            connStateElement.style.color = 'blue';
                            break;
                        case 4:
                            connStateElement.textContent = 'AUTHENTICATING';
                            connStateElement.style.color = 'blue';
                            break;
                        case 5:
                            connStateElement.textContent = 'ASSOCIATING';
                            connStateElement.style.color = 'blue';
                            break;
                        case 6:
                            connStateElement.textContent = 'ASSOCIATED';
                            connStateElement.style.color = 'green';
                            break;
                        case 7:
                            connStateElement.textContent = '4-WAY-HANDSHAKE';
                            connStateElement.style.color = 'blue';
                            break;
                        case 8:
                            connStateElement.textContent = '4-WAY-GROUP-HANDSHAKE';
                            connStateElement.style.color = 'blue';
                            break;
                        case 9:
                            connStateElement.textContent = 'CONNECTED TO AP';
                            connStateElement.style.color = 'green';
                            break;
                        default:
                            connStateElement.textContent = 'UNKNOWN';
                            connStateElement.style.color = 'black';
                            break;
                    }
                });
        }

        function loadWiFiSettings() {
            fetch('/load_wifi_settings')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        document.getElementById('wifi_ssid').value = data.ssid || '';
                        document.getElementById('wifi_pass').value = data.pass || '';
                    }
                });
        }

        function saveWiFiSettings() {
            const settings = {
                ssid: document.getElementById('wifi_ssid').value,
                pass: document.getElementById('wifi_pass').value
            };
            fetch('/save_wifi_settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            }).then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    if (confirm('WiFi settings saved successfully. Would you like to reboot now?')) {
                        rebootSystem();
                    } else {
                        alert('WiFi settings saved successfully.');
                    }
                } else {
                    alert('Failed to save WiFi settings.');
                }
            });
        }

        function runSiteSurvey() {
            fetch('/command?cmd=get&param=scan_list')
                .then(response => response.json())
                .then(data => {
                    const responseText = data.response.replace(/^RESP:\\d+\\s*/, '').trim();
                    const surveyResults = document.getElementById('surveyResults');
                    surveyResults.innerHTML = ''; // Clear previous results

                    const lines = responseText.split('\\n').slice(1); // Ignore the first line
                    lines.forEach(line => {
                        const [bssid, ssid, encryption, frequency, signal] = line.split(' ');
                        const row = document.createElement('tr');
                        row.innerHTML = `<td>${bssid}</td><td>${ssid}</td><td>${encryption}</td><td>${frequency}</td><td>${signal}</td>`;
                        surveyResults.appendChild(row);
                    });
                });
        }

        document.addEventListener('DOMContentLoaded', updateCommands);
        document.addEventListener('DOMContentLoaded', validateKeyMgmt);
        document.addEventListener('DOMContentLoaded', toggleApStaFields);
        document.addEventListener('DOMContentLoaded', loadStationSettings);
        document.addEventListener('DOMContentLoaded', loadWiFiSettings);
        document.addEventListener('DOMContentLoaded', () => {
            updateConnState();
            connStateInterval = setInterval(updateConnState, 5000);
        });
    </script>
    <script src="/static/jquery-3.5.1.min.js"></script>
    <script src="/static/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def run_command(command):
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).decode()
        output = re.sub(r'^RESP:\d+\s*', '', output)
    except subprocess.CalledProcessError as e:
        output = e.output.decode()
    return output

def load_last_settings():
    if os.path.exists(LAST_SETTINGS_FILE):
        with open(LAST_SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_settings(settings):
    with open(LAST_SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)

def apply_settings(settings):
    for key, value in settings.items():
        command = f"/sbin/hgpriv hg0 set {key}={value}"
        run_command(command)

def get_current_network_settings():
    ip_address = run_command("ifconfig hg0 | grep 'inet ' | awk '{print $2}'").strip()
    netmask = run_command("ifconfig hg0 | grep 'inet ' | awk '{print $4}'").strip()
    gateway = run_command("ip route | grep default | awk '{print $3}'").strip()
    return {'ip_address': ip_address, 'netmask': netmask, 'gateway': gateway}

def set_network_settings(ip_address, netmask, gateway):
    run_command(f"ifconfig hg0 {ip_address} netmask {netmask}")
    run_command(f"route add default gw {gateway}")

def load_station_settings():
    settings = {}
    if os.path.exists(CURRENT_SETTINGS_FILE):
        with open(CURRENT_SETTINGS_FILE, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    settings[key] = value.replace('\n', '')
    return settings

def save_station_settings_file(settings):
    backup_station_settings()
    with open(CURRENT_SETTINGS_FILE, 'w') as f:
        for key, value in settings.items():
            f.write(f"{key}={value}\n")

def backup_station_settings():
    if os.path.exists(CURRENT_SETTINGS_FILE):
        with open(CURRENT_SETTINGS_FILE, 'r') as src, open(BACKUP_SETTINGS_FILE, 'w') as dst:
            dst.write(src.read())

def restore_defaults():
    if os.path.exists(DEFAULT_SETTINGS_FILE):
        with open(DEFAULT_SETTINGS_FILE, 'r') as src, open(CURRENT_SETTINGS_FILE, 'w') as dst:
            dst.write(src.read())

def load_wifi_settings():
    ssid = ''
    password = ''
    if os.path.exists(WIFI_SSID_FILE):
        with open(WIFI_SSID_FILE, 'r') as f:
            ssid = f.read().strip()
    if os.path.exists(WIFI_PASS_FILE):
        with open(WIFI_PASS_FILE, 'r') as f:
            password = f.read().strip()
    return ssid, password

def save_wifi_settings(ssid, password):
    with open(WIFI_SSID_FILE, 'w') as f:
        f.write(ssid + '\n')
    with open(WIFI_PASS_FILE, 'w') as f:
        f.write(password + '\n')

@app.route('/')
def index():
    current_settings = {param: run_command(f"/sbin/hgpriv hg0 get {param}").strip() for param in ['ssid', 'bssid', 'txpower', 'bss_bw', 'conn_state']}
    current_network_settings = get_current_network_settings()
    return render_template_string(HTML_TEMPLATE, set_commands=SET_COMMANDS, get_commands=GET_COMMANDS, current_settings=current_settings, current_network_settings=current_network_settings)

@app.route('/command', methods=['GET'])
def handle_command():
    cmd_type = request.args.get('cmd')
    param = request.args.get('param')
    value = request.args.get('value')

    if cmd_type == 'get':
        command = f"/sbin/hgpriv hg0 get {param}"
    elif cmd_type == 'set':
        command = f"/sbin/hgpriv hg0 set {param}={value}"
    else:
        return jsonify({"response": "Invalid command type"})

    output = run_command(command)
    return jsonify({"response": output})

@app.route('/station_settings', methods=['POST'])
def save_station_settings():
    settings = request.json
    save_station_settings_file(settings)
    save_settings(settings)
    return jsonify({"status": "success"})

@app.route('/restore_defaults', methods=['POST'])
def handle_restore_defaults():
    restore_defaults()
    return jsonify({"status": "success"})

@app.route('/network_settings', methods=['POST'])
def save_network_settings():
    settings = request.json
    ip_address = settings.get('ip_address')
    netmask = settings.get('netmask')
    gateway = settings.get('gateway')
    if ip_address and netmask and gateway:
        set_network_settings(ip_address, netmask, gateway)
        return jsonify({"status": "success"})
    return jsonify({"status": "failure"})

@app.route('/load_station_settings', methods=['GET'])
def handle_load_station_settings():
    settings = load_station_settings()
    return jsonify({"status": "success", "settings": settings})

@app.route('/apply_last_settings', methods=['GET'])
def apply_last_settings():
    settings = load_last_settings()
    apply_settings(settings)
    return jsonify({"status": "success"})

@app.route('/quick_pair', methods=['POST'])
def quick_pair():
    run_command("/sbin/hgpriv hg0 set pairing=1")
    time.sleep(20)
    run_command("/sbin/hgpriv hg0 set pairing=0")
    return jsonify({"status": "success"})

@app.route('/reboot', methods=['POST'])
def reboot_system():
    run_command("reboot")
    return jsonify({"status": "success"})

@app.route('/run_command', methods=['POST'])
def run_system_command():
    command = request.json.get('command')
    if command:
        output = run_command(command)
        return jsonify({"status": "success", "output": output})
    return jsonify({"status": "failure"})

@app.route('/load_wifi_settings', methods=['GET'])
def handle_load_wifi_settings():
    ssid, password = load_wifi_settings()
    return jsonify({"status": "success", "ssid": ssid, "pass": password})

@app.route('/save_wifi_settings', methods=['POST'])
def handle_save_wifi_settings():
    settings = request.json
    ssid = settings.get('ssid')
    password = settings.get('pass')
    if ssid and password:
        save_wifi_settings(ssid, password)
        return jsonify({"status": "success"})
    return jsonify({"status": "failure"})

@app.route('/upload_firmware', methods=['POST'])
def upload_firmware():
    if 'firmware' not in request.files:
        return redirect(request.url)
    file = request.files['firmware']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        with open(filepath, 'rb') as f:
            firmware_data = f.read()
        with open('/proc/hgicf/ota', 'wb') as f:
            f.write(firmware_data)
        time.sleep(30)
        run_command("reboot")
        return jsonify({"status": "success"})
    return jsonify({"status": "failure"})

if __name__ == '__main__':
    last_settings = load_last_settings()
    if last_settings:
        apply_settings(last_settings)
    app.run(host='0.0.0.0', port=8080)

