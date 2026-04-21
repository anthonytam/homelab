#!/bin/sh
set -e

: "${NC_USER:?NC_USER is required}"
: "${NC_PASSWORD:?NC_PASSWORD is required}"
: "${NC_URL:?NC_URL is required}"

nextcloudcmd --non-interactive --user "${NC_USER}" --password "${NC_PASSWORD}" /nextcloud-data "${NC_URL}"