# status-api (karaoke-pipeline)

Exposes the status and health endpoints for the karaoke pipeline.  
Provides real-time and historical job status info via REST API.

## Features

- REST endpoints for health, job status, and pipeline metrics
- Integrates with Redis and `karaoke-shared` for status logic
- Minimal, stateless, lightweight service

## Usage

### Local Development

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export REDIS_HOST=localhost
python status_api.py
```

# TO BE CONTINUED...
