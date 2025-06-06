# karaoke-pipeline

Core microservices for the Karaoke Instrumental Pipeline.

## Services

- **volume-init**: Prepares required volumes for first use
- **watcher**: Detects new files and triggers pipeline
- **metadata**: Extracts and enriches track metadata
- **splitter**: Splits audio files into stems
- **packager**: Packages processed stems for delivery
- **organizer**: Organizes processed output for end users
- **status-api**: Status and health reporting API

## Usage

1. Clone this repo  
2. Copy `.env.example` to `.env` and set your environment variables  
3. Ensure all **named Docker volumes** and the `backend` network exist on the host:

    ```bash
    docker volume create input
    docker volume create queue
    docker volume create stems
    docker volume create output
    docker volume create organized
    docker volume create metadata
    docker volume create logs
    docker network create backend
    ```

4. Build and start the stack:

    ```bash
    docker compose up -d
    ```

## Notes

- All volumes/networks are **external** and can be shared across other repos.
- Each microservice can be developed and tested independently.
- See individual subdirectories for service-specific details.
