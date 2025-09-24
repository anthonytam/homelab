#!/bin/bash

docker build -t "ghcr.io/anthonytam/electrs:v$1" --build-arg VERSION=$1 .
