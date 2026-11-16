# Remote-site ingestion gateway

`alloy-gateway-ingest` uses the MetalLB address **10.200.12.13**, allocated
after checking the repository and live cluster Services. Create the desired
DNS A record pointing to this address before configuring remote collectors.

| Data | Remote Alloy destination | Internal destination |
| --- | --- | --- |
| Logs (`loki.write`) | `http://10.200.12.13:3100/loki/api/v1/push` | Loki gateway |
| Metrics (`prometheus.remote_write`) | `http://10.200.12.13:9999/api/v1/metrics/write` | Prometheus remote-write receiver |

Replace the IP in these URLs with the DNS name once it exists. The metric
ingestion path on Alloy differs from Prometheus's `/api/v1/write` path.

Remote collectors must attach `site="bombshelter"` or `site="cheesewheel"` to
both logs and metrics. The gateway preserves incoming labels and timestamps;
it does not relabel remote data as `thebridge`. Its existing Kubernetes event
collection continues to add `site="thebridge"` only to those local events.
Remote collector installation and configuration are a separate deployment.

These HTTP receivers have no authentication or TLS. Use private site routing
or a VPN and restrict network access to trusted collectors. Public exposure
requires a separate authenticated TLS ingress design. Site labels support
filtering but do not enforce account permissions or tenant isolation.

Only TCP 3100 and 9999 are exposed by this LoadBalancer. Alloy's management
port 12345 and the Loki/Prometheus backend Services remain internal. The
single gateway replica uses its existing PVC for the metrics WAL, and the
Recreate update strategy prevents concurrent writers during an upgrade.

Receiver references: [Loki push](https://grafana.com/docs/alloy/latest/reference/components/loki/loki.source.api/)
and [Prometheus remote write](https://grafana.com/docs/alloy/latest/reference/components/prometheus/prometheus.receive_http/).
