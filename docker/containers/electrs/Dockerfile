ARG VERSION=0.10.5

FROM rust:1.90.0 AS build
ARG VERSION
WORKDIR /build
RUN apt-get update && apt-get install -y wget clang libsnappy-dev

RUN wget https://github.com/romanz/electrs/archive/refs/tags/v${VERSION}.tar.gz \
 && tar xvf v${VERSION}.tar.gz \
 && cd electrs-${VERSION} \
 && cargo build --locked --release

FROM debian:trixie-slim
ARG VERSION
RUN apt update \
 && apt install -y adduser \
 && adduser --disabled-password --uid 1000 --home /app electrs
USER electrs
WORKDIR /app
COPY --from=build /build/electrs-${VERSION}/target/release/electrs /app/electrs
RUN mkdir /app/data

# RPC
EXPOSE 50001
# Prometheus
EXPOSE 4224

CMD ["/app/electrs"]
