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

## Credentials and activation

`snmp-auth-secret.sops.yaml` is encrypted to the existing Kubernetes SOPS PGP
recipient. Flux's platform Kustomization decrypts it into the
`alloy-local-snmp-auth` Secret. The pod mounts it read-only with group-readable
permissions for Alloy's existing UID/GID 473. Alloy reads it with
`local.file.is_secret = true`, which redacts it in the Alloy UI, and merges only
the private auth profile into the standard exporter modules. Credentials do not
appear in the target list or scrape URL.

The pfSense target is enabled after its passwords were populated locally.
Setting `"enabled": "false"` removes a target from the scrape list and prevents
polling, without changing or removing its authentication profile. Keep new
targets disabled until their real credentials are configured.

From the repository's `kubernetes` directory:

```sh
sops edit cluster/platform/monitoring/alloy-local/snmp-auth-secret.sops.yaml
```

Inside `stringData.snmp.yml`, set `password` to the NET-SNMP user's
authentication password and `priv_password` with its encryption passphrase.
Leave `username: alloy`, `version: 3`, `security_level: authPriv`,
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
