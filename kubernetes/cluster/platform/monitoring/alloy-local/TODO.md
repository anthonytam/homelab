# Appliance monitoring follow-ups

## pfSense

Baseline SNMPv3 polling is deployed for `pf01.local.tam.land` at
`10.200.11.1:161`. Defer the following work until a later monitoring iteration:

- [ ] Inventory the existing Zabbix pfSense checks and required notifications.
- [ ] Check NET-SNMP's available PF OIDs, then collect state-table usage/limit,
      state creation/removal, and relevant firewall error/drop counters. If
      needed, implement a persistent read-only helper and an Alloy SNMP module.
- [ ] Collect per-gateway dpinger status, latency, jitter, and packet loss.
- [ ] Collect VPN-specific tunnel/peer health and traffic for configured VPNs.
- [ ] Collect per-node CARP/VIP status if the firewall uses an HA pair.
- [ ] Add end-to-end connectivity probes, including destinations across the
      site-to-site tunnels. Route probes explicitly if testing individual WANs.
- [ ] Configure alert rules, notification routing, missing-data detection, and
      dashboards; verify required alerts before retiring matching Zabbix checks.

Before implementing appliance-side helpers, confirm the pfSense version,
gateway/VPN inventory, HA topology, and a supported way to persist the helpers.

## HypeStore physical disks

TrueNAS CORE runs as a VM with devices supplied by the HypeStore Linux
hypervisor. Collect physical-disk health on HypeStore, while TrueNAS supplies
the guest and ZFS pool/dataset/zvol metrics.

- [ ] Identify HypeStore's physical-disk/controller access and stable disk IDs.
- [ ] Collect SMART health, HDD temperatures, reallocated/pending/uncorrectable
      sectors, test results, and NVMe health where applicable, from HypeStore.
- [ ] Collect HypeStore kernel/controller I/O errors and correlate disk identities
      with the storage presented to TrueNAS.
- [ ] Add disk-health alerts and verify collection does not unnecessarily wake
      disks configured to sleep.
