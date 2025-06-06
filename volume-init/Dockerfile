FROM alpine:3.19

ARG PUID=1001
ARG PGID=1001

ENV PUID=${PUID}
ENV PGID=${PGID}

# Install coreutils for chown if not present (Alpine base has chown, but coreutils for more robust use if you ever need it)
RUN apk add --no-cache bash

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
