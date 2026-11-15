# Kubernetes and Talos logs

This Alloy DaemonSet collects pod logs through the Kubernetes API and Talos
service/kernel logs from a read-only host mount of `/var/log`. It runs on all
Talos nodes, including control planes and the peripheral worker.

The Talos reader matches only `/var/log/*.log`. It excludes rotated files and
the `pods` and `containers` directories, which prevents collecting pod logs twice.
Talos streams have `site="thebridge"`, `cluster="tamland"`, `source="talos"`,
`job="talos"`, `node`, `host`, `service` (the log filename without `.log`), and
`filename` labels. Original lines are preserved because service formats vary;
Loki timestamps represent collection time rather than parsed source timestamps.

New files start at the end on first discovery, so deployment does not backfill
existing logs. File positions are stored in `/var/lib/alloy-pod-logs` on each
node and survive Alloy pod replacement and normal node reboots. This is local
state, not replicated storage: node replacement or wiping that directory loses
positions. A newly discovered file also skips any lines written before discovery.
File positions are checkpoints, not a durable outbound log queue. Backend
outages and rotation can still lose logs; brief replay is possible after a crash.

No Talos machine configuration changes or syslog forwarding are needed.
Host metrics continue through the existing Prometheus node-exporter DaemonSet;
kubelet and container metrics continue through Prometheus. The node-exporter
Service label and node/cAdvisor scrape rules attach `site="thebridge"`.

Verify in Grafana Explore:

```logql
{site="thebridge", source="talos"}
{site="thebridge", source="talos", node="worker01", service="kubelet"}
```

Use the actual node name from Kubernetes for the second query. For metrics:

```promql
count(node_uname_info{site="thebridge"})
count by (job) (up{site="thebridge", job=~"kubernetes-nodes.*"})
```

This change adds labels to new samples only; older data retains its original
labels. The existing Kubernetes API pod-log reader has separate restart/replay
behavior and is unchanged by the Talos file checkpoints.
