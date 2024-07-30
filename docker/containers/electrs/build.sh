#!/bin/bash

docker build -t "registry.local.tam.land/anthonytam/electrs:v$1" --build-arg VERSION=$1 .
