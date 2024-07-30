ARG VERSION=27.1

FROM debian:bookworm-slim
ARG VERSION
WORKDIR /app
RUN apt-get update \
 && apt-get install -y git build-essential libtool autotools-dev automake pkg-config bsdmainutils python3 libevent-dev libboost-dev \
 && chown 1000 /app

RUN adduser --disabled-password --uid 1000 --home /app bitcoin
USER bitcoin

RUN git clone https://github.com/bitcoin/bitcoin.git \
 && cd bitcoin \
 && ./autogen.sh \
 && ./configure --disable-wallet \
 && make -j $(nproc --all) 

# RPC
EXPOSE 8332
# P2P
EXPOSE 8333

CMD ["/app/bitcoin/src/bitcoind"]
