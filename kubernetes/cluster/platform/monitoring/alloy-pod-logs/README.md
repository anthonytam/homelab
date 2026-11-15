# Kubernetes and Talos logs

This Alloy DaemonSet collects pod logs through the Kubernetes API and Talos
service/kernel logs from a read-only host mount of `/var/log`. It runs on all
Talos nodes, including control planes and the peripheral worker.

The Talos reader matches only `/var/log/*.log`. It excludes rotated files and
the `pods` and `containers` directories, which prevents collecting pod logs twice.
Talos streams have `site="thebridge"`, `cluster="tamland"`, `source="talos"`,
`job="talos"`, `node`, `host`, `service` (the log filename without `.log`), and
`filename` labels. ANSI colour codes are removed; log payloads are otherwise preserved.
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

## Severity classification

The Talos pipeline adds a bounded `level` label for new entries so Grafana can
classify these formats without relying on words inside the message:

| Format | Classification |
| --- | --- |
| Talos console logs, including coloured controller-runtime/DNS output | The explicit level after the ISO timestamp |
| JSON from etcd/containerd and other structured services | The top-level `level` field |
| Kubelet JSON without a level | A nonempty `err` field means error; otherwise a `msg` field means info |
| Klog text | `I`, `W`, `E`, `F` prefixes map to info, warn, error, fatal |
| Kernel logs | The explicit severity after `kern:`; notice maps to info |
| Machined RPC result lines | OK/Canceled map to info; Internal/Unavailable/Unknown/DataLoss/DeadlineExceeded/ResourceExhausted map to error; other recognized statuses map to warn |
| Audit records, authorization traces and unrecognized/malformed formats | unknown |

Machined's RPC mapping is a collection policy based on operation outcomes, not
a severity emitted by its logger. Its `rpc_code` label retains the original
bounded status value. For explicit levels, warning maps to warn, err to error,
panic/dpanic to fatal, and crit/alert/emerg to critical. Other severity values
remain unknown. A message mentioning an error does not override its source's
explicit info/debug severity.

Audit records describe security events rather than log severity. In particular,
an audit `success=no` is not automatically a system error; evaluate those records
with audit-specific queries or alerts. Unknown is an intentional classification
for records without enough information, not evidence of failed ingestion.

```logql
{site="thebridge", source="talos", level=~"warn|error|critical|fatal"}
{site="thebridge", source="talos", service="kubelet", level="error"}
{site="thebridge", source="talos", service="machined", rpc_code="PermissionDenied"}
```

The change does not reclassify historical entries. Inspect a recent time range
after the DaemonSet reloads when checking the new labels.
