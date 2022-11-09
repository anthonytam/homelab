#!/bin/bash
export GITHUB_TOKEN="<GITHUB_ACCESS_TOKEN>"
flux bootstrap github \
  --owner=anthonytam \
  --repository=homelab \
  --path=kubernetes/cluster/flux-bootstrap \
  --personal
