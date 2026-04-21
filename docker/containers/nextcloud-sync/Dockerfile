FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
COPY entrypoint.sh /entrypoint.sh
COPY sync.sh /sync.sh
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt update && \
    apt install -y --no-install-recommends \
      ca-certificates \
      gosu \
      software-properties-common && \
    add-apt-repository -y ppa:nextcloud-devs/client && \
    apt update && \
    apt install -y --no-install-recommends \
      nextcloud-client && \
    chmod +x /entrypoint.sh /sync.sh

ENTRYPOINT ["/entrypoint.sh"]