# The Bridge infrastructure collector

`alloy-local` receives logs and metrics from appliances and Linux/Windows agents
at **The Bridge**, the home-office site. It forwards logs to Loki and metrics to
Prometheus. Every pipeline sets `site="thebridge"`, replacing any client-supplied
`site` label. It does not collect host data itself or forward traces.

The dedicated MetalLB Service uses **10.200.12.12**, the next unallocated address
after `.11`, checked against repository assignments and live Services when added.
The existing Kubernetes events and pod-log collectors remain separate.

## Ingestion endpoints

| Input | Destination | Format |
| --- | --- | --- |
| Legacy syslog | `10.200.12.12:514` TCP or UDP | RFC3164 |
| Modern syslog | `10.200.12.12:1514` TCP or UDP | RFC5424 |
| Agent logs | `http://10.200.12.12:3100/loki/api/v1/push` | Loki push API |
| Agent metrics | `http://10.200.12.12:9999/api/v1/metrics/write` | Prometheus remote write v1 |
| OTLP logs/metrics | `10.200.12.12:4317` | OTLP gRPC without TLS |
| OTLP logs | `http://10.200.12.12:4318/v1/logs` | OTLP HTTP |
| OTLP metrics | `http://10.200.12.12:4318/v1/metrics` | OTLP HTTP |

Choose the syslog port to match the sender's format. Prefer TCP when supported.
The syslog receiver preserves message timestamps and exposes `host`, `app`,
`severity`, `facility`, and `source_ip` labels when available. RFC3164 timestamps
do not include a year or timezone; the collector assumes its current year and
local timezone (UTC in the container). RFC5424 includes timezone information.

The LoadBalancer routes syslog to unprivileged container ports, with
`externalTrafficPolicy: Local` to preserve the sender's network address.
Alloy's management interface on port 12345 remains internal to the cluster.
These ingestion endpoints are unauthenticated and intended for the local trusted
network. Site labels support filtering; they do not enforce account permissions
or backend tenant isolation.

## Host Alloy agents

Linux agents can collect journal/files and exporter metrics; Windows agents can
collect Windows Event Logs and Windows exporter metrics. Configure the agent's
existing collection components to use these forwarding destinations:

```alloy
loki.write "local_collector" {
  endpoint {
    url = "http://10.200.12.12:3100/loki/api/v1/push"
  }
}

prometheus.remote_write "local_collector" {
  endpoint {
    url = "http://10.200.12.12:9999/api/v1/metrics/write"
  }
}
```

Log components use `loki.write.local_collector.receiver`; metric components use
`prometheus.remote_write.local_collector.receiver`. Retain identifying labels
such as `host` for logs and `instance`/`job` for metrics. The collector stamps the
site centrally. OpenTelemetry agents can use the OTLP endpoints instead.

## Storage and deployment

The collector uses the same Alloy chart version as the other collectors and is
included in the monitoring Kustomization. Its 5 GiB PVC stores the Prometheus
remote-write WAL. A single replica with a `Recreate` rollout prevents concurrent
writers to the same WAL. Restarting or updating the collector briefly interrupts
ingestion, so host agents should retain their own queues/WALs.

The PVC does **not** enable durable log buffering: the Loki writer uses its
standard batching/retry behavior. UDP syslog has no delivery acknowledgment.
Use a sender-side disk spool if logs must survive receiver/backend outages.

After the manifests have been reconciled, check:

```sh
kubectl -n monitoring get helmrelease alloy-local
kubectl -n monitoring get deployment alloy-local
kubectl -n monitoring get service alloy-local-ingest
kubectl -n monitoring get endpointslice -l kubernetes.io/service-name=alloy-local-ingest
```

Query Loki with `{site="thebridge"}` or Prometheus with a metric selector such as
`up{site="thebridge"}` (when host agents scrape and forward that metric).
