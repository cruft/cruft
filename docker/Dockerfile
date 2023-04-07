FROM python:3.11.3-alpine

# Cruft version should be set from CI pipeline
ARG CRUFT_VERSION

RUN apk add --no-cache ca-certificates git

# Install cruft
COPY "dist/cruft-${CRUFT_VERSION}-py3-none-any.whl" "/tmp/cruft-${CRUFT_VERSION}-py3-none-any.whl"

ENV PATH="/opt/cruft:$PATH"

RUN set -eux; \
    pip3 install "/tmp/cruft-${CRUFT_VERSION}-py3-none-any.whl"; \
    cruft; \
    rm "/tmp/cruft-${CRUFT_VERSION}-py3-none-any.whl"


# Run cruft from unprivileged user
RUN set -eux; \
	addgroup -g 1234 -S cruft; \
	adduser -u 1234 -S -D -G cruft -H -h /home/cruft -s /bin/sh cruft; \
	mkdir -p /home/cruft; \
	chown -R cruft:cruft /home/cruft

USER cruft

ENTRYPOINT ["cruft"]
