# watcher (karaoke-pipeline)
Watches the input directory for new `.mp3` files and queues them for the pipeline.

## Features
- Monitors for new files and runs stability checks.
- Notifies pipeline of new work.
- Uses [karaoke-shared](https://github.com/svidal-nlive/karaoke-shared) for cross-service logic.

## Usage

### Local Development

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INPUT_DIR=./input
export QUEUE_DIR=./queue
python watcher.py
```

### Docker
```
docker build -t watcher .
docker run --rm \
  -e PUID=$(id -u) -e PGID=$(id -g) \
  -v $(pwd)/input:/input -v $(pwd)/queue:/queue \
  watcher
```

### With Compose
Make sure to set up the external Redis and backend network. Example compose file included.

## Environment Variables
- INPUT_DIR (default: /input)
- QUEUE_DIR (default: /queue)
- REDIS_HOST (default: redis)
- PUID, PGID for user IDs

## Shared Utilities
This service uses karaoke-shared (pip package) for pipeline utilities. See [karaoke-shared](https://github.com/svidal-nlive/karaoke-shared) for docs.
