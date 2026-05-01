#!/usr/bin/env python3
"""
FR24 Feeder → MQTT Bridge
Polls the FR24 feeder stats endpoint and publishes to MQTT with
Home Assistant discovery, grouping all entities under a single device.
"""

import json
import logging
import os
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("fr24_mqtt")

# ── Config from environment ───────────────────────────────────────────────────
FR24_URL        = os.environ.get("FR24_URL", "http://192.168.1.2/monitor.json")
MQTT_HOST       = os.environ.get("MQTT_HOST", "localhost")
MQTT_PORT       = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USER       = os.environ.get("MQTT_USER", "")
MQTT_PASS       = os.environ.get("MQTT_PASS", "")
POLL_INTERVAL   = int(os.environ.get("POLL_INTERVAL", "30"))
DISCOVERY_PREFIX = os.environ.get("DISCOVERY_PREFIX", "homeassistant")
STATE_TOPIC     = "fr24/state"
AVAILABILITY_TOPIC = "fr24/availability"
DEVICE_ID       = "fr24_feeder"

# ── Device definition (shared across all entities) ────────────────────────────
DEVICE = {
    "identifiers": [DEVICE_ID],
    "name": "FlightRadar24 Feeder",
    "manufacturer": "Flightradar24",
    "model": "FR24Feed",
    "configuration_url": FR24_URL.rsplit("/", 1)[0],
}

# ── Sensor definitions ────────────────────────────────────────────────────────
# Format: (unique_id_suffix, friendly_name, value_template, extra_config_dict)
SENSORS = [
    # ── Aircraft counts ───────────────────────────────────────────────────────
    (
        "ac_tracked",
        "Aircraft Tracked",
        "{{ value_json.feed_num_ac_tracked | int }}",
        {"unit_of_measurement": "aircraft", "state_class": "measurement", "icon": "mdi:airplane"},
    ),
    (
        "ac_adsb_tracked",
        "ADS-B Aircraft Tracked",
        "{{ value_json.feed_num_ac_adsb_tracked | int }}",
        {"unit_of_measurement": "aircraft", "state_class": "measurement", "icon": "mdi:airplane-check"},
    ),
    (
        "ac_non_adsb_tracked",
        "Non-ADS-B Aircraft Tracked",
        "{{ value_json.feed_num_ac_non_adsb_tracked | int }}",
        {"unit_of_measurement": "aircraft", "state_class": "measurement", "icon": "mdi:airplane-remove"},
    ),
    (
        "ac_map_size",
        "AC Map Size",
        "{{ value_json.ac_map_size | int }}",
        {"state_class": "measurement", "icon": "mdi:map"},
    ),
    (
        "d11_map_size",
        "D11 Map Size",
        "{{ value_json.d11_map_size | int }}",
        {"state_class": "measurement", "icon": "mdi:map"},
    ),
    # ── Feed status ───────────────────────────────────────────────────────────
    (
        "feed_status",
        "Feed Status",
        "{{ value_json.feed_status }}",
        {"icon": "mdi:antenna"},
    ),
    (
        "feed_status_message",
        "Feed Status Message",
        "{{ value_json.feed_status_message }}",
        {"icon": "mdi:message-alert"},
    ),
    (
        "feed_alias",
        "Feed Alias",
        "{{ value_json.feed_alias }}",
        {"icon": "mdi:tag"},
    ),
    (
        "feed_type",
        "Feed Type",
        "{{ value_json.feed_type }}",
        {"icon": "mdi:access-point"},
    ),
    (
        "feed_legacy_id",
        "Feed Legacy ID",
        "{{ value_json.feed_legacy_id }}",
        {"icon": "mdi:identifier"},
    ),
    (
        "feed_current_server",
        "Feed Current Server",
        "{{ value_json.feed_current_server }}",
        {"icon": "mdi:server-network"},
    ),
    (
        "feed_configured_mode",
        "Feed Configured Mode",
        "{{ value_json.feed_configured_mode }}",
        {"icon": "mdi:swap-horizontal"},
    ),
    (
        "feed_current_mode",
        "Feed Current Mode",
        "{{ value_json.feed_current_mode }}",
        {"icon": "mdi:swap-horizontal"},
    ),
    (
        "feed_last_config_result",
        "Feed Last Config Result",
        "{{ value_json.feed_last_config_result }}",
        {"icon": "mdi:cog-sync"},
    ),
    (
        "feed_last_ac_sent_num",
        "Feed Last AC Sent Count",
        "{{ value_json.feed_last_ac_sent_num | int }}",
        {"unit_of_measurement": "aircraft", "state_class": "measurement", "icon": "mdi:send"},
    ),
    # ── Message stats ─────────────────────────────────────────────────────────
    (
        "num_messages",
        "Messages Received",
        "{{ value_json.num_messages | int }}",
        {"unit_of_measurement": "messages", "state_class": "total_increasing", "icon": "mdi:message-processing"},
    ),
    (
        "num_resyncs",
        "Resyncs",
        "{{ value_json.num_resyncs | int }}",
        {"state_class": "total_increasing", "icon": "mdi:sync"},
    ),
    (
        "num_global_timeouts",
        "Global Timeouts",
        "{{ value_json.num_global_timeouts | int }}",
        {"state_class": "total_increasing", "icon": "mdi:timer-off"},
    ),
    (
        "msg_ring_length",
        "Message Ring Length",
        "{{ value_json.msg_ring_length | int }}",
        {"state_class": "measurement", "icon": "mdi:buffer"},
    ),
    (
        "dns_queries",
        "DNS Queries",
        "{{ value_json.dns_queries | int }}",
        {"state_class": "total_increasing", "icon": "mdi:dns"},
    ),
    (
        "ntp_queries",
        "NTP Queries",
        "{{ value_json.ntp_queries | int }}",
        {"state_class": "total_increasing", "icon": "mdi:clock-check"},
    ),
    (
        "open_fds",
        "Open File Descriptors",
        "{{ value_json.open_fds | int }}",
        {"state_class": "measurement", "icon": "mdi:file-multiple"},
    ),
    # ── Receiver ─────────────────────────────────────────────────────────────
    (
        "rx_connected",
        "Receiver Connected",
        "{{ value_json.rx_connected | int }}",
        {"icon": "mdi:usb-port"},
    ),
    (
        "last_rx_connect_status",
        "Receiver Last Connect Status",
        "{{ value_json.last_rx_connect_status }}",
        {"icon": "mdi:connection"},
    ),
    (
        "last_rx_connect_time_s",
        "Receiver Last Connect Time",
        "{{ value_json.last_rx_connect_time_s }}",
        {"device_class": "timestamp", "icon": "mdi:clock-in"},
    ),
    # ── Timing ───────────────────────────────────────────────────────────────
    (
        "timing_source",
        "Timing Source",
        "{{ value_json.timing_source }}",
        {"icon": "mdi:clock-check"},
    ),
    (
        "timing_is_valid",
        "Timing Valid",
        "{{ value_json.timing_is_valid | int }}",
        {"icon": "mdi:clock-check-outline"},
    ),
    (
        "timing_last_result",
        "Timing Last Result",
        "{{ value_json.timing_last_result }}",
        {"icon": "mdi:clock-sync-outline"},
    ),
    (
        "timing_last_drift",
        "Timing Last Drift",
        "{{ value_json.timing_last_drift | float }}",
        {"unit_of_measurement": "s", "state_class": "measurement", "icon": "mdi:clock-alert"},
    ),
    (
        "timing_last_offset",
        "Timing Last Offset",
        "{{ value_json.timing_last_offset | float }}",
        {"unit_of_measurement": "s", "state_class": "measurement", "icon": "mdi:clock-alert-outline"},
    ),
    (
        "timing_time_since_last_success",
        "Timing Since Last Success",
        "{{ value_json.timing_time_since_last_success | int }}",
        {"unit_of_measurement": "s", "state_class": "measurement", "icon": "mdi:timer"},
    ),
    (
        "timestamp_source",
        "Timestamp Source",
        "{{ value_json.timestamp_source }}",
        {"icon": "mdi:clock-digital"},
    ),
    (
        "time_update_utc_s",
        "Last Time Update",
        "{{ value_json.time_update_utc_s }}",
        {"icon": "mdi:update"},
    ),
    # ── MLAT ─────────────────────────────────────────────────────────────────
    (
        "mlat_ok",
        "MLAT Status",
        "{{ value_json['mlat-ok'] }}",
        {"icon": "mdi:map-marker-radius"},
    ),
    (
        "mlat_started",
        "MLAT Started",
        "{{ value_json['mlat-started'] }}",
        {"icon": "mdi:play-circle"},
    ),
    (
        "mlat_problem",
        "MLAT Problem",
        "{{ value_json.mlat_problem }}",
        {"icon": "mdi:alert-circle"},
    ),
    # ── Build info ────────────────────────────────────────────────────────────
    (
        "build_version",
        "Build Version",
        "{{ value_json.build_version }}",
        {"icon": "mdi:information"},
    ),
    (
        "build_arch",
        "Build Architecture",
        "{{ value_json.build_arch }}",
        {"icon": "mdi:chip"},
    ),
    (
        "build_os",
        "Build OS",
        "{{ value_json.build_os }}",
        {"icon": "mdi:linux"},
    ),
    (
        "build_revision",
        "Build Revision",
        "{{ value_json.build_revision }}",
        {"icon": "mdi:source-commit"},
    ),
    (
        "build_flavour",
        "Build Flavour",
        "{{ value_json.build_flavour }}",
        {"icon": "mdi:tag-text"},
    ),
    # ── Receiver config ───────────────────────────────────────────────────────
    (
        "cfg_receiver",
        "Receiver Type",
        "{{ value_json.cfg_receiver }}",
        {"icon": "mdi:radio-tower"},
    ),
    (
        "cfg_bs",
        "Beast Output Enabled",
        "{{ value_json.cfg_bs }}",
        {"icon": "mdi:toggle-switch"},
    ),
    (
        "cfg_raw",
        "Raw Output Enabled",
        "{{ value_json.cfg_raw }}",
        {"icon": "mdi:toggle-switch"},
    ),
    (
        "cfg_mpx",
        "MPX Enabled",
        "{{ value_json.cfg_mpx }}",
        {"icon": "mdi:toggle-switch"},
    ),
    # ── Misc ──────────────────────────────────────────────────────────────────
    (
        "local_ips",
        "Local IPs",
        "{{ value_json.local_ips }}",
        {"icon": "mdi:ip-network"},
    ),
    (
        "offline_mode",
        "Offline Mode",
        "{{ value_json['offline-mode'] }}",
        {"icon": "mdi:cloud-off"},
    ),
    (
        "extended_ui",
        "Extended UI",
        "{{ value_json.extended_ui }}",
        {"icon": "mdi:monitor-dashboard"},
    ),
    (
        "wifi_allowed",
        "WiFi Allowed",
        "{{ value_json.wifi_allowed | int }}",
        {"icon": "mdi:wifi"},
    ),
    (
        "gps_tods",
        "GPS ToDs",
        "{{ value_json.gps_tods | int }}",
        {"icon": "mdi:crosshairs-gps"},
    ),
    (
        "local_tods",
        "Local ToDs",
        "{{ value_json.local_tods | int }}",
        {"icon": "mdi:timer-outline"},
    ),
    (
        "df_stats",
        "DF Stats",
        "{{ value_json['df-stats'] }}",
        {"icon": "mdi:chart-bar"},
    ),
]

# ── Binary sensors ────────────────────────────────────────────────────────────
BINARY_SENSORS = [
    (
        "feed_connected",
        "Feed Connected",
        "{{ value_json.feed_status == 'connected' }}",
        {"device_class": "connectivity"},
    ),
    (
        "rx_connected_binary",
        "Receiver Connected",
        "{{ value_json.rx_connected == '1' }}",
        {"device_class": "connectivity"},
    ),
    (
        "timing_valid",
        "Timing Valid",
        "{{ value_json.timing_is_valid == '1' }}",
        {"device_class": "problem", "icon": "mdi:clock-check"},
        # inverted: timing_is_valid=0 means problem
    ),
    (
        "msg_ring_full",
        "Message Ring Full",
        "{{ value_json.msg_ring_full == 'true' }}",
        {"device_class": "problem"},
    ),
    (
        "shutdown",
        "Shutdown Requested",
        "{{ value_json.shutdown == 'yes' }}",
        {"device_class": "problem"},
    ),
]


def build_discovery_payload(unique_id, name, value_template, extra, entity_type="sensor"):
    payload = {
        "name": name,
        "unique_id": f"{DEVICE_ID}_{unique_id}",
        "state_topic": STATE_TOPIC,
        "availability_topic": AVAILABILITY_TOPIC,
        "value_template": value_template,
        "device": DEVICE,
    }
    payload.update(extra)
    return payload


def publish_discovery(client, sw_version=None):
    if sw_version and DEVICE.get("sw_version") != sw_version:
        DEVICE["sw_version"] = sw_version

    for uid, name, tmpl, extra in SENSORS:
        topic = f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}/{uid}/config"
        payload = build_discovery_payload(uid, name, tmpl, extra, "sensor")
        client.publish(topic, json.dumps(payload), retain=True)
        log.debug("Published discovery: %s", topic)

    for uid, name, tmpl, extra in BINARY_SENSORS:
        topic = f"{DISCOVERY_PREFIX}/binary_sensor/{DEVICE_ID}/{uid}/config"
        payload = build_discovery_payload(uid, name, tmpl, extra, "binary_sensor")
        client.publish(topic, json.dumps(payload), retain=True)
        log.debug("Published discovery: %s", topic)

    log.info("Discovery published: %d sensors, %d binary sensors", len(SENSORS), len(BINARY_SENSORS))


def fetch_fr24():
    resp = requests.get(FR24_URL, timeout=10)
    resp.raise_for_status()
    return resp.json()


def main():
    client = mqtt.Client(client_id="fr24_mqtt_bridge", clean_session=True)
    client.will_set(AVAILABILITY_TOPIC, payload="offline", retain=True)

    if MQTT_USER:
        client.username_pw_set(MQTT_USER, MQTT_PASS)

    log.info("Connecting to MQTT broker %s:%d", MQTT_HOST, MQTT_PORT)
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()

    discovery_published = False
    consecutive_errors = 0

    while True:
        try:
            data = fetch_fr24()

            # Publish discovery on first success (or if sw_version changes)
            sw_version = data.get("build_version")
            if not discovery_published:
                publish_discovery(client, sw_version)
                discovery_published = True
            elif sw_version != DEVICE.get("sw_version"):
                log.info("Version changed to %s, republishing discovery", sw_version)
                publish_discovery(client, sw_version)

            client.publish(AVAILABILITY_TOPIC, "online", retain=True)
            client.publish(STATE_TOPIC, json.dumps(data))
            log.info(
                "Published state — tracked: %s ac, messages: %s, feed: %s",
                data.get("feed_num_ac_tracked", "?"),
                data.get("num_messages", "?"),
                data.get("feed_status", "?"),
            )
            consecutive_errors = 0

        except requests.RequestException as e:
            consecutive_errors += 1
            log.warning("FR24 fetch failed (%d consecutive): %s", consecutive_errors, e)
            if consecutive_errors >= 3:
                client.publish(AVAILABILITY_TOPIC, "offline", retain=True)

        except Exception as e:
            log.error("Unexpected error: %s", e, exc_info=True)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
