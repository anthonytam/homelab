# HPE iLO 4 hardware monitoring

The existing `alloy-local` deployment polls these management interfaces over
UDP 161 every 60 seconds. No exporter pod, additional agent, or inbound
LoadBalancer port is needed.

| iLO target | Address | Server model | Firmware | SOPS auth profile |
| --- | --- | --- | --- | --- |
| ilo-hype01.local.tam.land | 10.200.200.2 | ProLiant DL360e Gen8 | 2.82 | ilo_hype01_v3 |
| ilo-hypestore.local.tam.land | 10.200.200.3 | ProLiant DL380p Gen8 | 2.82 | ilo_hypestore_v3 |

## iLO settings

Use **Administration → Management → SNMP Settings**, select **Agentless
Management**, and configure an SNMPv3 user on each iLO:

- Security Name: `alloy`.
- Authentication Protocol: **SHA**.
- Privacy Protocol: **AES**.
- Set authentication and privacy passphrases; iLO 4 accepts 8–49 characters.
- Enable SNMP access on UDP port 161. The Alloy scrape uses `authPriv`.

SNMPv3 users are separate from iLO web-login accounts. Use each target's own
profile in `snmp-auth-secret.sops.yaml`, encrypted with the existing SOPS key.
Leave the pfSense and TrueNAS profiles unchanged when editing iLO credentials.
Targets remain disabled until credentials are populated; `enabled: "false"`
removes a target from the scrape list and prevents requests.

Allow UDP 161 from the collector's actual cluster egress addresses to the iLO
management VLAN. The inbound telemetry VIP 10.200.12.12 is not a fixed SNMP
source address. No trap receiver is required for polling.

## Collection and limits

Each target uses `system,hpe_ilo4`. The focused module in `snmp-modules.yaml`
includes 36 metric definitions, using explicit scalar GETs and column walks:

- Overall server-health, thermal, iLO and Smart Array conditions.
- CPU hardware condition, memory-module size/status/correctable-error condition.
- Per-sensor temperatures, shutdown thresholds, conditions and hardware locations.
- Per-fan presence, condition, redundancy and speed class.
- PSU presence, condition, error status, capacity/use and redundancy.
- Current server power consumption and server power state.
- Smart Array controller, logical-drive and physical-drive conditions/status,
  and drive temperatures where available.

Numeric indices are retained, with sensor/fan/PSU/DIMM location lookup labels
where the agent supplies them. Firmware, platform, installed hardware and AMS
determine which OIDs return data. A successful scrape does not imply every
optional metric is available. Polling does not configure alert rules or traps.

Important interpretation details:

- `cpqHeMibCondition` and most `*Condition` metrics use **1 other/unknown,
  2 OK, 3 degraded, 4 failed**. Check the metric's `enum_values` before applying
  that mapping to other status fields.
- `cpqHeResMem2ModuleCondition` value **4** means degraded with an unknown module
  index; it is not the generic failed state. Memory-module `Status` uses another
  enumeration, including **4 good** and **12 spare**.
- `cpqHeFltTolPowerSupplyStatus` uses **1 noError**; its `Condition` uses **2 OK**.
- `cpqHeFltTolFanSpeed` is an enum (**1 other, 2 normal, 3 high**), not RPM or
  percentage. No numeric fan-speed measurement is claimed.
- Temperatures are degrees Celsius; `cpqHeTemperatureCelsius == -99` means
  unavailable. Power readings/capacities are watts; memory-module size is KiB.
- Storage visibility depends on the controller mode and AMS. These metrics
  complement HypeStore's planned full SMART/error monitoring. They do not
  replace it or TrueNAS ZFS pool/dataset metrics.
- iLO remains reachable independently of the host OS. Some hardware-health
  values can reflect the last powered-on state when the server is off.

The initial authenticated checks returned 30 temperature sensors and 8 fans on
Hype01, and 36 temperature sensors and 6 fans on HypeStore. Both returned two
PSU entries and memory-module health. Neither returned CPQIDA physical-drive
status series with its current hardware/AMS configuration. Missing storage
series must not be interpreted as healthy drives.

The profile copies selected definitions from Alloy v1.16.3's embedded HPE
module and adds health/fan/memory definitions checked against HPE's
[MIB archive](https://downloads.hpe.com/pub/softlib2/software1/pubsw-linux/p1580676047/v229101/upd11.85mib.tar.gz).
The archive checksum is recorded in `snmp-modules.yaml`.

## Verification

All series include `site="thebridge"`, `job="integrations/snmp"`,
`device_type="ilo4"`, `source="snmp"`, and the individual iLO's FQDN in `host`.
`instance` is the iLO FQDN plus `:161`; `server` identifies the corresponding
host for correlation with OS metrics.

```promql
up{site="thebridge", job="integrations/snmp", device_type="ilo4"}
cpqHeMibCondition{site="thebridge", device_type="ilo4"}
cpqHeTemperatureCelsius{site="thebridge", device_type="ilo4"} >= 0
cpqHeFltTolFanCondition{site="thebridge", device_type="ilo4"}
cpqHeFltTolPowerSupplyCondition{site="thebridge", device_type="ilo4"}
cpqHePowerMeterCurrReading{site="thebridge", device_type="ilo4"}
cpqHeResMem2ModuleCondition{site="thebridge", device_type="ilo4"}
```

Expect `up == 1` for each enabled target. Alloy's own healthy endpoint confirms
configuration validity; only live scrape results confirm device availability.

## Remote syslog

On **Administration → Management → Remote Syslog**, enable remote syslog,
set **Remote Syslog Server** to `telemetry.local.tam.land`, and set
**Remote Syslog Port** to **1514**. Apply the settings. iLO 4 firmware 2.82 was
observed sending **RFC 5424 over UDP**; the collector's external port 514 is for
RFC 3164 and rejects these messages. External UDP 1514 maps to container port
2514, where Alloy's RFC 5424 listener runs.

Remote syslog requires an iLO license supporting the feature. It forwards new
iLO Event Log and IML events; it does not import historical events. A browser
logout/login produces an iLO event suitable for an ingestion check.

Alloy retains the RFC 5424 timestamp, so configure working SNTP servers under
**Network → iLO Dedicated Network Port** (or **Shared Network Port**) → **SNTP**.
Verify the emitted UTC time agrees with actual UTC time. The initial HypeStore
capture was about one hour behind; use a wider Grafana time range until the
device clock is corrected.

Syslog's `host` comes from the iLO's configured hostname and can differ in case
or domain from its SNMP target FQDN. Query by the preserved source IP when
checking initial ingestion:

```logql
{site="thebridge", source="syslog", source_ip=~"10[.]200[.]200[.][23]"}
```
