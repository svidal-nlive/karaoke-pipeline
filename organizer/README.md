# organizer (karaoke-pipeline)

Handles the organization and movement of files in the karaoke processing pipeline.  
Can move, rename, or archive processed content for efficient downstream access.

## Features
- Organizes and archives completed jobs
- Moves files to next pipeline stage or storage
- Uses [karaoke-shared](https://github.com/svidal-nlive/karaoke-shared) for shared logic/utilities

## Usage

### Local Development

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INPUT_DIR=./input
export OUTPUT_DIR=./output
export REDIS_HOST=localhost
python organizer.py
```

# TO BE CONTINUED...
