# splitter (karaoke-pipeline)

Performs vocal/instrumental stem separation using [Spleeter](https://github.com/deezer/spleeter).

## Features
- Runs Spleeter to extract 2, 4, or 5 stems per track.
- Uses [karaoke-shared](https://github.com/svidal-nlive/karaoke-shared) for pipeline integration and common utilities.
- Communicates via Redis, shares output via local or cloud storage.

## Usage

### Local Development

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INPUT_DIR=./input
export OUTPUT_DIR=./output
export REDIS_HOST=localhost
python splitter.py
```

### Docker
```
docker build -t splitter .
docker run --rm \
  -e PUID=$(id -u) -e PGID=$(id -g) \
  -e INPUT_DIR=/input \
  -e OUTPUT_DIR=/output \
  -e REDIS_HOST=redis \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  splitter
```

### With Compose
Make sure to set up the external Redis and backend network. Example compose file included.

## Environment Variables
- INPUT_DIR (default: /input)
- OUTPUT_DIR (default: /output)
- REDIS_HOST (default: redis)
- PUID, PGID (default: 1000)

## Shared Utilities
This service uses karaoke-shared (pip package) for pipeline utilities. See [karaoke-shared](https://github.com/svidal-nlive/karaoke-shared) for docs.
