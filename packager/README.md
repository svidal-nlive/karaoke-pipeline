# packager (karaoke-pipeline)

Bundles processed stems and metadata into a single package for delivery.  
Typical output: .zip files, ready for download or cloud storage.

## Features
- Combines stems, metadata, and cover images.
- Uses [karaoke-shared](https://github.com/svidal-nlive/karaoke-shared) for common utilities.
- Integrates with pipeline via Redis and local/cloud storage.

## Usage

### Local Development

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INPUT_DIR=./input
export OUTPUT_DIR=./output
export REDIS_HOST=localhost
python packager.py
```

### Docker
```
docker build -t packager .
docker run --rm \
  -e PUID=$(id -u) -e PGID=$(id -g) \
  -e INPUT_DIR=/input \
  -e OUTPUT_DIR=/output \
  -e REDIS_HOST=redis \
  -v $(pwd)/input:/input \
  -v $(pwd)/output:/output \
  packager
```

### With Compose
Make sure to set up the external Redis and backend network. Example compose file included.

## Environment Variables
- INPUT_DIR (default: /input)
- OUTPUT_DIR (default: /output)
- REDIS_HOST (default: redis)
- PUID, PGID for user IDs

## Shared Utilities
This service uses karaoke-shared (pip package) for pipeline utilities. See [karaoke-shared](https://github.com/svidal-nlive/karaoke-shared) for docs.
