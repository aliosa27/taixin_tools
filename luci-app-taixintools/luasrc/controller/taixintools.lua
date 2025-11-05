module("luci.controller.taixintools", package.seeall)

function index()
    entry({"admin", "network", "taixintools"}, alias("admin", "network", "taixintools", "netat"), _("TaixinTools"), 60).dependent = false

    entry({"admin", "network", "taixintools", "netat"}, template("taixintools/netat"), _("NetAT Commands"), 1)
    entry({"admin", "network", "taixintools", "netlog"}, template("taixintools/netlog"), _("NetLog Viewer"), 2)
    entry({"admin", "network", "taixintools", "signal"}, template("taixintools/signal"), _("Signal Monitor"), 3)

    -- API endpoints
    entry({"admin", "network", "taixintools", "get_interfaces"}, call("get_interfaces"), nil)
    entry({"admin", "network", "taixintools", "scan_devices"}, call("scan_devices"), nil)
    entry({"admin", "network", "taixintools", "send_command"}, call("send_command"), nil)
    entry({"admin", "network", "taixintools", "start_netlog"}, call("start_netlog"), nil)
    entry({"admin", "network", "taixintools", "stop_netlog"}, call("stop_netlog"), nil)
    entry({"admin", "network", "taixintools", "get_netlog"}, call("get_netlog"), nil)
    entry({"admin", "network", "taixintools", "save_config"}, call("save_config"), nil)
    entry({"admin", "network", "taixintools", "load_config"}, call("load_config"), nil)
    entry({"admin", "network", "taixintools", "get_signal"}, call("get_signal"), nil)
end

function get_interfaces()
    luci.http.prepare_content("application/json")

    local interfaces = {}
    local f = io.popen("ip link show | grep -E '^[0-9]+:' | awk -F': ' '{print $2}'")
    if f then
        for line in f:lines() do
            table.insert(interfaces, line)
        end
        f:close()
    end

    -- Check if hg0 exists
    local has_hg0 = false
    for _, iface in ipairs(interfaces) do
        if iface == "hg0" then
            has_hg0 = true
            break
        end
    end

    luci.http.write_json({
        interfaces = interfaces,
        has_hg0 = has_hg0,
        default_interface = has_hg0 and "hg0" or nil
    })
end

function scan_devices()
    luci.http.prepare_content("application/json")

    local interface = luci.http.formvalue("interface")

    if not interface or interface == "" then
        luci.http.write_json({success = false, error = "Interface is required"})
        return
    end

    -- Execute scan
    local cmd = string.format("/usr/lib/taixintools/netat_scan.sh '%s'", interface:gsub("'", "'\\''"))
    local handle = io.popen(cmd .. " 2>&1")
    local result = handle:read("*a")
    local success = handle:close()

    -- Parse device list from output
    local devices = {}
    local seen = {}
    for line in result:gmatch("[^\r\n]+") do
        -- Look for MAC addresses in format aa:bb:cc:dd:ee:ff
        local mac = line:match("([0-9a-f][0-9a-f]:[0-9a-f][0-9a-f]:[0-9a-f][0-9a-f]:[0-9a-f][0-9a-f]:[0-9a-f][0-9a-f]:[0-9a-f][0-9a-f])")
        if mac and not seen[mac] then
            seen[mac] = true
            table.insert(devices, mac)
        end
    end

    luci.http.write_json({
        success = success,
        devices = devices,
        output = result
    })
end

function send_command()
    luci.http.prepare_content("application/json")

    local command = luci.http.formvalue("command")
    local interface = luci.http.formvalue("interface")
    local device = luci.http.formvalue("device")

    if not command or command == "" then
        luci.http.write_json({success = false, error = "Command is required"})
        return
    end

    if not interface or interface == "" then
        luci.http.write_json({success = false, error = "Interface is required"})
        return
    end

    if not device or device == "" then
        luci.http.write_json({success = false, error = "Device MAC is required"})
        return
    end

    -- Execute the netat command via backend script with device MAC
    local cmd = string.format("/usr/lib/taixintools/netat_send.sh '%s' '%s' '%s'",
        interface:gsub("'", "'\\''"), device:gsub("'", "'\\''"), command:gsub("'", "'\\''"))
    local handle = io.popen(cmd .. " 2>&1")
    local result = handle:read("*a")
    local success = handle:close()

    luci.http.write_json({
        success = success,
        output = result
    })
end

function start_netlog()
    luci.http.prepare_content("application/json")

    local interface = luci.http.formvalue("interface")
    local device = luci.http.formvalue("device")

    if not interface or interface == "" then
        luci.http.write_json({success = false, error = "Interface is required"})
        return
    end

    if not device or device == "" then
        luci.http.write_json({success = false, error = "Device MAC is required"})
        return
    end

    -- Start netlog capture with device MAC
    local cmd = string.format("/usr/lib/taixintools/netlog_start.sh '%s' '%s'",
        interface:gsub("'", "'\\''"), device:gsub("'", "'\\''"))
    local handle = io.popen(cmd .. " 2>&1")
    local result = handle:read("*a")
    local success = handle:close()

    luci.http.write_json({
        success = success,
        output = result
    })
end

function stop_netlog()
    luci.http.prepare_content("application/json")

    local handle = io.popen("/usr/lib/taixintools/netlog_stop.sh 2>&1")
    local result = handle:read("*a")
    local success = handle:close()

    luci.http.write_json({
        success = success,
        output = result
    })
end

function get_netlog()
    luci.http.prepare_content("application/json")

    -- Read the latest netlog output
    local handle = io.popen("/usr/lib/taixintools/netlog_read.sh 2>&1")
    local result = handle:read("*a")
    handle:close()

    luci.http.write_json({
        logs = result
    })
end

function save_config()
    luci.http.prepare_content("application/json")

    local firmware_version = luci.http.formvalue("firmware_version")
    local mode = luci.http.formvalue("mode")
    local ssid = luci.http.formvalue("ssid")
    local keymgmt = luci.http.formvalue("keymgmt")
    local psk = luci.http.formvalue("psk")
    local encrypt = luci.http.formvalue("encrypt")
    local key = luci.http.formvalue("key")
    local bandwidth = luci.http.formvalue("bandwidth")
    local channels = luci.http.formvalue("channels")
    local device = luci.http.formvalue("device")

    if not mode or not ssid then
        luci.http.write_json({success = false, error = "Missing required fields"})
        return
    end

    local uci = require("luci.model.uci").cursor()

    uci:set("taixintools", "saved_config", "device_config")
    uci:set("taixintools", "saved_config", "firmware_version", firmware_version or "2x")
    uci:set("taixintools", "saved_config", "mode", mode)
    uci:set("taixintools", "saved_config", "ssid", ssid)
    uci:set("taixintools", "saved_config", "keymgmt", keymgmt or "wpa-psk")
    uci:set("taixintools", "saved_config", "psk", psk or "")
    uci:set("taixintools", "saved_config", "encrypt", encrypt or "1")
    uci:set("taixintools", "saved_config", "key", key or "")
    uci:set("taixintools", "saved_config", "bandwidth", bandwidth or "2")
    uci:set("taixintools", "saved_config", "channels", channels or "")
    uci:set("taixintools", "saved_config", "last_device", device or "")

    uci:commit("taixintools")

    luci.http.write_json({
        success = true,
        message = "Configuration saved"
    })
end

function load_config()
    luci.http.prepare_content("application/json")

    local uci = require("luci.model.uci").cursor()

    local firmware_version = uci:get("taixintools", "saved_config", "firmware_version") or "2x"
    local mode = uci:get("taixintools", "saved_config", "mode") or "1"
    local ssid = uci:get("taixintools", "saved_config", "ssid") or ""
    local keymgmt = uci:get("taixintools", "saved_config", "keymgmt") or "wpa-psk"
    local psk = uci:get("taixintools", "saved_config", "psk") or ""
    local encrypt = uci:get("taixintools", "saved_config", "encrypt") or "1"
    local key = uci:get("taixintools", "saved_config", "key") or ""
    local bandwidth = uci:get("taixintools", "saved_config", "bandwidth") or "2"
    local channels = uci:get("taixintools", "saved_config", "channels") or ""
    local device = uci:get("taixintools", "saved_config", "last_device") or ""

    luci.http.write_json({
        success = true,
        config = {
            firmware_version = firmware_version,
            mode = mode,
            ssid = ssid,
            keymgmt = keymgmt,
            psk = psk,
            encrypt = encrypt,
            key = key,
            bandwidth = bandwidth,
            channels = channels,
            last_device = device
        }
    })
end

function get_signal()
    luci.http.prepare_content("application/json")

    local interface = luci.http.formvalue("interface")
    local device = luci.http.formvalue("device")

    if not interface or interface == "" then
        luci.http.write_json({success = false, error = "Interface is required"})
        return
    end

    if not device or device == "" then
        luci.http.write_json({success = false, error = "Device MAC is required"})
        return
    end

    -- Get RSSI value
    local cmd = string.format("/usr/lib/taixintools/netat_send.sh '%s' '%s' 'at+rssi?'",
        interface:gsub("'", "'\\''"), device:gsub("'", "'\\''"))
    local handle = io.popen(cmd .. " 2>&1")
    local result = handle:read("*a")
    local success = handle:close()

    -- Parse RSSI value from output (format: "Response: -45" or "RSSI: -45")
    local rssi = nil
    for line in result:gmatch("[^\r\n]+") do
        -- Try "Response: -45" format first
        local value = line:match("Response:%s*(-?%d+)")
        if not value then
            -- Fall back to "RSSI: -45" format
            value = line:match("RSSI:%s*(-?%d+)")
        end
        if value then
            rssi = tonumber(value)
            break
        end
    end

    luci.http.write_json({
        success = success and rssi ~= nil,
        rssi = rssi,
        output = result
    })
end
