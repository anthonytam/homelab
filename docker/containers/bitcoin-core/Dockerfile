ARG VERSION=27.1

FROM debian:bookworm-slim
ARG VERSION
WORKDIR /app
RUN apt-get update \
 && apt-get install -y git build-essential cmake pkgconf python3 libevent-dev libboost-dev libcapnp-dev capnproto libzmq3-dev systemtap-sdt-dev  \
 && chown 1000 /app

RUN adduser --disabled-password --uid 1000 --home /app bitcoin
USER bitcoin

RUN git clone https://github.com/bitcoin/bitcoin.git \
 && cd bitcoin \
 && cmake -B build -DENABLE_WALLET=OFF \
 && cmake --build build -j $(nproc --all)

# RPC
EXPOSE 8332
# P2P
EXPOSE 8333

CMD ["/app/bitcoin/bin/bitcoind"]
