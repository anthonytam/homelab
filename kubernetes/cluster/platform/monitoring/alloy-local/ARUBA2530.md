# HP/Aruba 2530 monitoring

| Switch | Management address | Model | Firmware | SOPS profile |
| --- | --- | --- | --- | --- |
| BMT-ACS01-HP-2530.local.tam.land | 10.200.200.200 | HP 2530-48G-PoE+-2SFP+ (J9853A) | YA.16.11.0024 | bmt_acs01_hp_2530_v3 |

This switch runs ArubaOS-Switch, with different CLI commands, hardware MIBs
and syslog behavior from the Comware 5130. The existing `alloy-local` instance
polls it every 60 seconds over UDP 161. Credentials are SHA-1/AES-128 with
`authPriv`, encrypted in `snmp-auth-secret.sops.yaml`.

## Switch configuration

Enter an SSH or console session with manager privileges:

```text
configure terminal
snmpv3 enable
```

When first enabling SNMPv3, its interactive setup creates an `initial` user.
Set strong temporary passwords locally, decline the optional additional SHA
user because `alloy` is created explicitly below, and decline changes to
v1/v2 access while migrating an existing Zabbix poller.

Choose distinct authentication/privacy passphrases, preferably 16–32 visible
characters without spaces. Use the same values under this switch's SOPS
profile and replace the placeholders locally:

```text
snmpv3 user alloy auth sha AUTH_PASSPHRASE priv aes PRIV_PASSPHRASE
snmpv3 group operatorauth user alloy sec-model ver3
logging 10.200.12.12 udp
logging origin-id hostname
logging severity info
debug destination logging
debug event
write memory
```

`operatorauth` provides OperatorReadView and a limited DiscoveryView write
view; it does not grant general switch configuration writes. The predefined
operator group requires authentication, while Alloy requests authentication
and privacy with SHA/AES. Do not substitute `managerpriv`, which grants
configuration write access, just to obtain a privacy-requiring group.

**UDP 514 is implicit** in `logging 10.200.12.12 udp`. This firmware rejects
an explicitly supplied port 514: its explicit-port range is 1024–65535.
The destination is `telemetry.local.tam.land`'s IP to avoid switch DNS
dependency. Logging origin-id uses the switch hostname, without an FQDN.
Informational-and-higher Event Log messages are forwarded. These `debug`
commands select Event Log forwarding, not all packet/protocol debug streams.

After successful authenticated v3 polling, disable older versions and remove
the bootstrap user:

```text
configure terminal
snmpv3 only
no snmpv3 user initial
write memory
```

`snmpv3 only` blocks v1/v2c requests, including the old Zabbix configuration.
It does not delete stored community definitions. The user requested this
cutover after the v3 profile was configured. No Alloy trap receiver is needed.

Read-only verification commands, without showing passphrases or communities:

```text
show snmpv3 enable
show snmpv3 user
show snmpv3 group
show snmpv3 only
show debug
```

Log out and back in to generate a fresh event. Existing historical Event Log
entries are not imported. Allow UDP 514 from the switch to 10.200.12.12 and
UDP 161 from the collector's actual cluster egress addresses to the switch.
The inbound telemetry VIP is not a fixed source address for SNMP requests.

## Metrics and interpretation

The target uses `system,if_mib,hp_procurve,hp_procurve_poe`. The two focused
custom modules supplement the bundled system/interface modules with:

- CPU utilization in percent and installed/free/allocated memory in bytes.
- Hardware sensor status and warning/failure counters, with description labels.
- Standard PoE detection state, priority/classification, disconnect/fault/
  power-denied counters, PSE capacity/consumption and operational state.
- HP per-port PoE supplied power in **milliwatts** and current in **milliamperes**.
- Optional numeric air-temperature/threshold and over-temperature fields,
  only when the agent supplies them.

The initial SHA/AES scrape returned 72 interface entries (including logical
interfaces), CPU and memory, two hardware sensor states, 48 PoE port states,
48 private per-port power readings and one total PSE power reading. No numeric
chassis-temperature series were returned; do not treat absence as zero or
claim numeric temperature coverage. Optional non-numeric temperature fields
produce no numeric sample.

`hpicfSensorStatus` uses **1 unknown, 2 bad, 3 warning, 4 good, 5 notPresent**.
Do not apply iLO or Comware status mappings. Absence must be interpreted
against the installed hardware. Sensor failure/warning counters describe
transitions, while the current status reports present state. Standard PoE
power is watts; divide `hpicfPoePethPsePortPower` by 1000 for watts and
`hpicfPoePethPsePortCurrent` by 1000 for amperes. PoE group/port indexes are
retained and are not assumed to equal IF-MIB `ifIndex`.

Modules request selected scalar/column OIDs, avoiding a full enterprise walk.
They use vendor-authored HP MIB definitions mirrored in LibreNMS at pinned
revision `c5c3425c484d891510587f7c8c3727b5ace67b59`; checksums are recorded
in `snmp-modules.yaml`. Existing Comware and server modules remain separate.

## Ingestion checks

Metrics include `site="thebridge"`, `job="integrations/snmp"`,
`device_type="hp_procurve"`, `source="snmp"`, and the DNS FQDN in `host`.

```promql
up{host="BMT-ACS01-HP-2530.local.tam.land", job="integrations/snmp"}
hpSwitchCpuStat{host="BMT-ACS01-HP-2530.local.tam.land"}
hpicfSensorStatus{host="BMT-ACS01-HP-2530.local.tam.land"}
hpicfPoePethPsePortPower{host="BMT-ACS01-HP-2530.local.tam.land"} / 1000
```

Syslog was verified on the existing **RFC 3164 UDP 514** listener. It includes
`host="BMT-ACS01-HP-2530"`, severity, sender IP and site labels. It does not
need the Comware raw-input listener on 5514. Receipt time avoids timezone
ambiguity in the device timestamp. The event-number-prefixed payload can
leave the standard parser's app label unset; the original message body is
still retained.

```logql
{site="thebridge", source="syslog", host="BMT-ACS01-HP-2530"}
```

## References

- [2530 management and configuration guide, 16.11](https://arubanetworking.hpe.com/techdocs/AOS-Switch/16.11/Aruba%202530%20Management%20and%20Configuration%20Guide%20for%20AOS-S%2016.11.pdf).
- [Vendor MIB definitions at the pinned mirror revision](https://github.com/librenms/librenms/tree/c5c3425c484d891510587f7c8c3727b5ace67b59/mibs/hp): HP-ICF-CHASSIS, HP-ICF-POE-MIB, HP-ICF-OID, NETSWITCH-MIB and STATISTICS-MIB.
