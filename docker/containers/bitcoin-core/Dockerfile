ARG VERSION=v27.1

FROM ubuntu:24.04 AS build
ARG VERSION
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /src
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && \
    apt-get install -y --no-install-recommends \
      ca-certificates \
      git \
      build-essential \
      cmake \
      pkg-config \
      python3 \
      libevent-dev \
      libboost-dev \
      libcapnp-dev \
      capnproto \
      libzmq3-dev \
      systemtap-sdt-dev \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --branch "${VERSION}" --depth 1 --single-branch https://github.com/bitcoin/bitcoin.git
WORKDIR /src/bitcoin
RUN cmake -S . -B build -DENABLE_WALLET=OFF && \
    cmake --build build -j "$(nproc)"


FROM ubuntu:24.04 AS runtime
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ca-certificates \
      libevent-2.1-7t64 \
      libzmq5 \
      libboost-chrono1.83.0 \
      libboost-filesystem1.83.0 \
      libboost-program-options1.83.0 \
      libboost-system1.83.0 \
      libboost-thread1.83.0 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -g 10001 bitcoin && \
    useradd -m -u 10001 -g 10001 -s /usr/sbin/nologin bitcoin

WORKDIR /app
COPY --from=build /src/bitcoin/build/bin/bitcoind /app/bitcoind
COPY --from=build /src/bitcoin/build/bin/bitcoin-cli /app/bitcoin-cli

RUN mkdir -p /data && chown -R bitcoin:bitcoin /data /app
USER bitcoin

EXPOSE 8332 8333
VOLUME ["/data"]
CMD ["/app/bitcoind", "-datadir=/data"]
