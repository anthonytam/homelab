This wasnt fun...

The create and drop jobs were generated using the instruction here:
https://github.com/frappe/helm/blob/main/erpnext/README.md#create-new-site
https://github.com/frappe/helm/blob/main/erpnext/README.md#drop-site

However, between using Flux "valuesFrom" and other issues, they don't generate nicely. The custom-values.yaml file is filled in manually and used to generate the jobs via

```shell
helm template frappe-bench -n erpnext frappe/erpnext -f custom-values.yaml -s templates/job-create-site.yaml > create-new-site-job.yaml
helm template frappe-bench -n erpnext frappe/erpnext -f custom-values.yaml -s templates/job-drop-site.yaml > job-drop-site.yaml
```

These output files then required further modifications (SA and Namespace) to get executing correctly. Leaving it all here with REDACTED notes where a secret was removed to hopefully make it easier next time.

JUST in case, also leaving a copy of the frappe/helm README here from commit e1027bacebb4164a0f1f9695bcdb203f2b30c5d8 in the event its removed/modified at some point and doesnt work with the instance running here.
