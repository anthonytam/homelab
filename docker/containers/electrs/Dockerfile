ARG VERSION=0.10.5

FROM rust:1.92.0 AS build
ARG VERSION
WORKDIR /build
ENV DEBIAN_FRONTEND=noninteractive
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        build-essential \
        libclang-dev \
        libsnappy-dev \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/romanz/electrs/archive/refs/tags/v${VERSION}.tar.gz \
 && tar xvf v${VERSION}.tar.gz \
 && cd electrs-${VERSION} \
 && cargo build --locked --release

FROM ubuntu:24.04 AS runtime
ARG VERSION
ENV DEBIAN_FRONTEND=noninteractive

ARG UID=10001
ARG GID=10001

RUN groupadd -g ${GID} electrs && \
    useradd -m -u ${UID} -g ${GID} -s /usr/sbin/nologin electrs

WORKDIR /app
RUN mkdir -p /app/data && chown -R electrs:electrs /app
COPY --from=build /build/electrs-${VERSION}/target/release/electrs /app/electrs

USER electrs

# RPC
EXPOSE 50001
# Prometheus
EXPOSE 4224

CMD ["/app/electrs"]
