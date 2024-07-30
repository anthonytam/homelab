#!/bin/bash

docker build -t "registry.local.tam.land/anthonytam/bitcoind:v$1" --build-arg VERSION=$1 .
