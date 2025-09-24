#!/bin/bash

docker build -t "ghcr.io/anthonytam/bitcoind:v$1" --build-arg VERSION=$1 .
