FROM cgr.dev/chainguard/python:3.11.3-dev as builder

# Cruft version should be set from CI pipeline
ARG CRUFT_VERSION

# Install cruft
COPY "dist/cruft-${CRUFT_VERSION}-py3-none-any.whl" "/tmp/cruft-${CRUFT_VERSION}-py3-none-any.whl"

ENV PYTHONPATH="/app/cruft:$PYTHONPATH"

WORKDIR /app

RUN set -eux; \
    pip install --target="/app/cruft" "/tmp/cruft-${CRUFT_VERSION}-py3-none-any.whl"; \
    /app/cruft/bin/cruft

FROM cgr.dev/chainguard/python:3.11.3-dev

WORKDIR /cruft

COPY --from=builder /app/cruft .

ENV PATH="/cruft/bin/:$PATH"
ENV PYTHONPATH="/cruft:$PYTHONPATH"

WORKDIR /app

ENTRYPOINT ["cruft"]
