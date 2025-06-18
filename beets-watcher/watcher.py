import time
import os
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

MUSIC_INPUT = "/music/input"
BEETS_CONFIG = os.environ.get("BEETS_CONFIG", "/config/config.yaml")

class ImportHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(".mp3"):
            print(f"Detected new file: {event.src_path} — Importing to Beets...")
            try:
                subprocess.run(
                    ["beet", "-c", BEETS_CONFIG, "import", "--quiet", "--move", "--copy=no", event.src_path],
                    check=True,
                )
                print("Import complete!")
            except Exception as e:
                print(f"Import failed: {e}")

if __name__ == "__main__":
    print(f"Watching {MUSIC_INPUT} for new files...")
    observer = Observer()
    observer.schedule(ImportHandler(), MUSIC_INPUT, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
