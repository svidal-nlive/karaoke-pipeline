# volume-init

**One-shot container to set correct ownership/permissions for all shared Docker volumes.**  
Run this service **before** launching the main pipeline stack to avoid permission issues.

## Usage

### In Compose

```
services:
  volume-init:
    build: ./volume-init
    environment:
      - PUID=1000
      - PGID=1000
    user: "0:0"
    command: []
    volumes:
      - input:/input
      - queue:/queue
      - logs:/logs
      - metadata:/metadata
      - output:/output
      - organized:/organized
      - stems:/stems
      - cookies:/cookies
      - playwright_profile:/profile
    restart: "no"

Standalone

docker build -t volume-init .
docker run --rm \
  -e PUID=$(id -u) \
  -e PGID=$(id -g) \
  -v input:/input \
  -v queue:/queue \
  ... \
  volume-init

Environment Variables

PUID – user ID to set as owner

PGID – group ID


Notes

No dependencies or packages needed—shell only!

Safe to run repeatedly (idempotent).

Can be used as an initContainer in k8s as well.
