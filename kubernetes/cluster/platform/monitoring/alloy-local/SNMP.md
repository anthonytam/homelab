# Appliance SNMP polling

The single `alloy-local` deployment polls appliances using its embedded SNMP
exporter, scrapes the results every 60 seconds, and forwards them through the
existing site-label and Prometheus remote-write pipeline. No additional listener,
LoadBalancer port, RBAC permission, or DaemonSet is required.

## pfSense target

`snmp-config.yaml` defines `pf01.local.tam.land`, polled at **10.200.11.1:161/UDP**.
Use this address because it is the configured NET-SNMP binding; the firewall's
DNS record resolves to another interface. The SNMPv3 user is `alloy`, using
`authPriv`, SHA authentication, and AES encryption. NET-SNMP's user must have
read-only access and minimum security level Private (Encryption Required).

The selected modules are embedded in Alloy v1.16.3: `system`, `if_mib`, `hrDevice`,
`hrStorage`, `hrSystem`, `ucd_memory`, `ucd_system_stats`, and `ucd_la_table`.
They cover system identity/uptime, interface status/counters/errors/discards,
processor load, storage allocation/use, memory, CPU counters, and load averages.
Available series depend on the agent and its enabled instrumentation. In
particular, NET-SNMP must have load monitoring configured to expose load averages.

This profile does not claim PF states/rules/queues, gateway quality, VPN health,
or CARP coverage. The built-in bsnmpd PF module does not automatically configure
the replacement NET-SNMP agent. Check available OIDs before adding a PF module;
these gaps must be addressed before retiring equivalent Zabbix checks.

## TrueNAS CORE target

`truenas.local.tam.land:161/UDP` uses its own `truenas_v3` authentication
profile with SHA/AES `authPriv`. Its `host` is `truenas.local.tam.land`,
`device_type` is `truenas`, and `site` is `thebridge`.

It uses the same standard modules as pfSense plus `truenas_core13` from
`snmp-modules.yaml`. The custom module collects pool health, capacity and
cumulative logical I/O counters, dataset and zvol capacity, and ZFS ARC/L2ARC
statistics. Pool, dataset and zvol names are retained as labels. It is pinned to
the **CORE 13.0-U6.8 FREENAS-MIB** and its agent implementation; reassess the
module before upgrading or migrating to SCALE.

Important units and semantics:

- Pool, dataset and zvol capacity values require multiplication by their
  matching `AllocationUnits` metric to obtain bytes. These units are dynamic.
- The custom ARC/L2ARC metrics ending in `_bytes` already convert the agent's
  KiB values to bytes. Percentage metrics range from 0 to 100.
- `zpoolHealth == 0` means online; 1 degraded, 2 faulted, 3 offline, 4 unavailable,
  and 5 removed. Pool I/O metrics are cumulative counters; use `rate()`.
- CORE exposes ARC hit/miss counters as 32-bit values, so they can wrap.
- Dataset capacity shares pool space; summing dataset sizes double-counts it.

For example, in Grafana Explore:

```promql
up{site="thebridge", host="truenas.local.tam.land", job="integrations/snmp"}
zpoolHealth{site="thebridge", host="truenas.local.tam.land"}
zpoolSize{site="thebridge", host="truenas.local.tam.land"}
  * zpoolAllocationUnits{site="thebridge", host="truenas.local.tam.land"}
100 * zpoolUsed{site="thebridge", host="truenas.local.tam.land"}
  / zpoolSize{site="thebridge", host="truenas.local.tam.land"}
rate(zpoolReadBytes{site="thebridge", host="truenas.local.tam.land"}[5m])
truenas_zfs_arc_size_bytes{site="thebridge", host="truenas.local.tam.land"}
```

TrueNAS syslog uses the existing RFC 3164 listener at
`telemetry.local.tam.land:514`, using TCP or UDP to match the appliance setting.
Alloy extracts the hostname carried in the message into `host`; it also retains
`source_ip`, `syslog_format="rfc3164"`, and `site="thebridge"`. The supplied
hostname may be short rather than fully qualified. Find streams with:

```logql
{site="thebridge", source="syslog", syslog_format="rfc3164"}
```

RFC 3164 headers carry local time without a timezone or year. The collector uses
receipt time for these logs so a Toronto timestamp is not interpreted as UTC
and shifted several hours into the past. RFC 5424 listeners retain the supplied
timestamp, which includes its timezone. CORE can include the original logger's
RFC 5424 timestamp inside the forwarded message body; that text is preserved.

If forwarding is absent, check DNS and the generated configuration on TrueNAS:

```sh
getent hosts telemetry.local.tam.land
service syslog-ng onestatus
tail -n 5 /etc/local/syslog-ng.conf
```

The generated file should end with a `destination loghost` block for UDP/TCP
port 514 and a `log` rule using `filter(f_info)`. Info includes errors and higher
severities. Save the settings in System → Advanced. If the generated file is
stale, use the middleware to regenerate it and restart the service as root:

```sh
midclt call etc.generate syslogd
midclt call service.restart syslogd
logger -p user.err -t alloy-test "TrueNAS forwarding test"
```

Physical-disk temperatures, SMART status and hardware/controller errors belong
to the **HypeStore Linux hypervisor**. This module does not walk the HDD
temperature or LM-SENSORS branches. See `TODO.md` for that follow-up. Native
TrueNAS alerts, replication/job results and full ZFS error/scrub details also
need separate coverage before retiring their Zabbix checks.

Mappings and units were checked against the release's
[FREENAS-MIB](https://github.com/truenas/middleware/blob/5021f909d2f5476f918a185d87d66b958477028f/src/freenas/usr/local/share/snmp/mibs/FREENAS-MIB.txt)
and [SNMP agent](https://github.com/truenas/middleware/blob/5021f909d2f5476f918a185d87d66b958477028f/src/freenas/usr/local/bin/snmp-agent.py).

## HPE iLO 4 targets

`ilo-hype01.local.tam.land` (DL360e Gen8) and
`ilo-hypestore.local.tam.land` (DL380p Gen8), both running iLO 4 firmware 2.82,
use independent SNMPv3 profiles and the focused `hpe_ilo4` module. See
[ILO4.md](ILO4.md) for setup, hardware coverage, status semantics, and queries.

## Credentials and activation

`snmp-auth-secret.sops.yaml` is encrypted to the existing Kubernetes SOPS PGP
recipient. Flux's platform Kustomization decrypts it into the
`alloy-local-snmp-auth` Secret. The pod mounts it read-only with group-readable
permissions for Alloy's existing UID/GID 473. Alloy reads it with
`local.file.is_secret = true`, which redacts it in the Alloy UI, and merges only
the private auth profiles and custom module into the standard exporter modules. Credentials do not
appear in the target list or scrape URL.

Appliance targets are enabled only after their passwords are populated locally.
Setting `"enabled": "false"` removes a target from the scrape list and prevents
polling, without changing or removing its authentication profile. Keep new
targets disabled until their real credentials are configured.

From the repository's `kubernetes` directory:

```sh
sops edit cluster/platform/monitoring/alloy-local/snmp-auth-secret.sops.yaml
```

Inside the relevant profile in `stringData.snmp.yml`, set `password` to the SNMP user's
authentication password and `priv_password` with its encryption passphrase.
Use the appliance's username (currently `alloy`), `version: 3`, `security_level: authPriv`,
`auth_protocol: SHA`, and `priv_protocol: AES` intact. Save and close the editor;
SOPS re-encrypts the Secret. Do not commit decrypted copies.

For a new target, after setting both passwords, set its `enabled` string to `"true"` in
`snmp-config.yaml`. Commit and push the encrypted Secret and target change
together so Flux can reconcile them. Whole-directory projections permit updates
without a pod restart; allow for Kubernetes projection and Alloy file reload.
The initial addition of the mounts does restart the collector and briefly
interrupts ingestion.

pfSense must allow UDP 161 to its **10.200.11.1** address from the collector's
actual cluster egress address. The inbound LoadBalancer VIP 10.200.12.12 is not
a fixed outbound source. The pod may move between workers; choose the firewall
rule based on observed egress and the cluster's masquerading/routing policy.

## Verification

In Grafana Explore, query:

```promql
up{site="thebridge", job="integrations/snmp", host="pf01.local.tam.land"}
ifHCInOctets{site="thebridge", host="pf01.local.tam.land"}
hrProcessorLoad{site="thebridge", host="pf01.local.tam.land"}
memTotalReal{site="thebridge", host="pf01.local.tam.land"}
hrStorageUsed{site="thebridge", host="pf01.local.tam.land"}
```

Once enabled, `up` should be 1. While disabled there is no scrape target and no
new `up` series. An exporter component reporting healthy means its configuration
loaded, not that the appliance responded successfully.

All series include `site="thebridge"`, `job="integrations/snmp"`,
`instance="10.200.11.1:161"`, `host="pf01.local.tam.land"`,
`device_type="pfsense"`, and `source="snmp"`. Interface metrics additionally
retain their index/name/alias labels when the agent provides them. Values use
the SNMP exporter's native units: interface octets are bytes, UCD memory is
typically KiB, and storage size/use require multiplication by
`hrStorageAllocationUnits` to obtain bytes.

When adding switches or other appliances, add a target with its own module list,
device identity, and authentication profile. Keep additional credentials in the
SOPS Secret, and enable only confirmed targets. Do not duplicate these polls in
the node-local Alloy DaemonSet.
