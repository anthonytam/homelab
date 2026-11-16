# HPE Comware switch monitoring

The existing `alloy-local` collector polls SNMP over UDP 161 every 60 seconds.
The switch forwards syslog to `telemetry.local.tam.land` (10.200.12.12) over
UDP 514. No additional exporter deployment or inbound SNMP service is needed.

| Switch | Management IP | Model | Firmware | Topology | SOPS auth profile |
| --- | --- | --- | --- | --- | --- |
| UPS-ACS01-HP-5130.local.tam.land | 10.200.200.201 | HPE 5130 24G PoE+ 4SFP+ EI | Comware 7.1.070, Release 3507-US | Standalone | ups_acs01_hp_5130_v3 |

## Switch configuration

Choose two distinct authentication/privacy passphrases, preferably 16–32 visible
characters without spaces. Enter them locally in place of `AUTH_PASSPHRASE`
and `PRIV_PASSPHRASE` below. Configure the same values under the switch's
profile in `snmp-auth-secret.sops.yaml` using `sops edit`. The passwords must
remain out of Git plaintext, chat, and diagnostic output.

These commands configure a VACM group with read-only access to the standard
and Comware MIB trees, SNMPv3 authentication/privacy using SHA-1/AES-128, and
informational-and-higher syslog. No monitoring was configured on this switch
when it was added; selecting v3 alone does not preserve a legacy v1/v2c poller.

```text
system-view
snmp-agent
snmp-agent sys-info version v3
snmp-agent mib-view included alloy-read 1.3.6.1.2.1
snmp-agent mib-view included alloy-read 1.3.6.1.4.1.25506
snmp-agent group v3 alloy-ro privacy read-view alloy-read
snmp-agent usm-user v3 alloy alloy-ro simple authentication-mode sha AUTH_PASSPHRASE privacy-mode aes128 PRIV_PASSPHRASE

info-center enable
info-center source default loghost level informational
info-center timestamp loghost no-year-date
info-center loghost 10.200.12.12 port 514 facility local7
quit
save safely
```

Confirm the save prompt. The destination IP avoids a dependency on switch DNS.
Comware's default loghost timestamp includes a year in a non-RFC-3164 position;
`no-year-date` selects the BSD-style timestamp expected by the external port
514 listener. That listener assigns receipt time, retaining the original
message body. ISO timestamps alone do not make a message RFC 5424.

Permit collector egress to the management address on UDP 161, and switch
egress to 10.200.12.12 on UDP 514. The telemetry VIP is an inbound address;
SNMP requests do not necessarily originate from 10.200.12.12. Any source ACL
must allow the actual cluster egress addresses across collector rescheduling.
No SNMP trap destination is required for polling.

Read-only checks, without displaying passwords or the full configuration:

```text
display snmp-agent sys-info version
display snmp-agent group alloy-ro
display snmp-agent usm-user username alloy
display info-center
```

Log out and back into the switch to generate a login event for the initial
syslog check. Existing buffered logs are not replayed to the collector.

## Collection

The target uses `system,if_mib,hpe_comware,hpe_comware_poe`:

- System identity/uptime and interface names, aliases, speeds, traffic counters,
  errors, discards, administrative status, and operational status.
- Comware CPU/memory utilization, temperatures and their thresholds, physical
  entity classes, and entity operating/error states for hardware health.
- Standard PoE port enabled/detection state, priority/classification, fault and
  power-denied counters, total PSE power/capacity and operational status.
- Comware PoE port current/average/peak power and configured power limits.

The custom modules request selected columns, including ENTITY-MIB name and
description lookups. They do not walk the entire enterprise tree. Firmware and
installed hardware determine which optional metrics return data; a successful
scrape does not prove that every listed sensor is supported. Validate the
returned series before building dashboards or alerts. Temperature value 65535
means unavailable on the 5130 EI and must not be treated as a real temperature.

The standard PoE power readings are watts. Private `hh3cPsePort*Power` and
`hh3cPsePortPowerLimit` values retain their native **milliwatts**; divide by
1000 for watts. PoE has a group index and a port index; neither is assumed to
equal IF-MIB `ifIndex`. Establish the mapping from observed data before joining
port traffic and PoE metrics. CPU/memory values are percentages, not fractions.

Entity error status is an enumeration, not a boolean: 2 is normal, 3 is POST
failure, 4 is absent, and other codes describe specific hardware faults.
Absence must be interpreted against installed hardware. Entity operating
status uses a different enumeration: 1 unsupported, 2 disabled, 3 enabled,
4 dangerous. Do not apply iLO condition mappings to Comware metrics.

Targets stay disabled (`enabled: "false"`) until credentials and switch
configuration are ready. The discovery filter removes disabled targets from
the scrape list, so they produce no polls. Enable the target only after an
authenticated read-only check succeeds.

The initial authenticated check on Release 3507-US returned 32 interface
entries, 24 PoE port detection/current-power entries, one total PSE power
reading, and CPU, memory, temperature and entity health series. The target
is enabled after this check. This does not establish alerting coverage.

## Verification

Metrics inherit `site="thebridge"`, `job="integrations/snmp"`,
`device_type="hpe_comware"`, `source="snmp"`, and the switch FQDN in `host`.

```promql
up{site="thebridge", job="integrations/snmp", device_type="hpe_comware"}
ifHCInOctets{host="UPS-ACS01-HP-5130.local.tam.land"}
hh3cEntityExtCpuUsage{host="UPS-ACS01-HP-5130.local.tam.land"}
hh3cEntityExtTemperature{host="UPS-ACS01-HP-5130.local.tam.land"} < 65535
hh3cPsePortCurrentPower{host="UPS-ACS01-HP-5130.local.tam.land"} / 1000
pethMainPseConsumptionPower{host="UPS-ACS01-HP-5130.local.tam.land"}
```

Syslog's `host` comes from the switch's sysname, which can differ from its DNS
name. Its source IP follows routing unless a specific loghost source interface
is configured. Start with:

```logql
{site="thebridge", source="syslog", source_ip="10.200.200.201"}
```

Alloy configuration health and local parser checks establish configuration
validity; live `up == 1` plus current Loki entries establish ingestion.

## References

- [H3C S5130-EI network management command reference](https://www.h3c.com/en/Support/Resource_Center/HK/Switches/H3C_S5130/H3C_S5130_Series_Switches/Technical_Documents/Reference_Guides/Command_References/H3C_S5130-EI_CR-Release_311x-6W102/10/201803/1073831_294551_0.htm).
- [HPE 5130 EI Comware 7 MIB companion](https://arubanetworking.hpe.com/techdocs/comware/MIB_files/HPE5130EICmwr7MIBCompanion.pdf).
- [POWER-ETHERNET-MIB](https://www.h3c.com/en/d_202603/2774558_294551_0.htm) and [HH3C-POWER-ETH-EXT-MIB](https://wwwsg.h3c.com/en/d_202603/2773995_294551_0.htm) define the PoE indexes and units. Those reference pages cover newer H3C products; their MIB definitions do not establish support on this switch's firmware.
