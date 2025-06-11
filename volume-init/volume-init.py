#!/usr/bin/env python3
import os
import pwd
import grp
import sys

DIRS = [
    "/input",
    "/queue",
    "/logs",
    "/metadata",
    "/output",
    "/organized",
    "/stems",
    "/cookies",
    "/chromium_config",
    "/profile",
]

def log(msg):
    print(msg, flush=True)

def parse_uid_gid():
    puid = int(os.environ.get("PUID", "1000"))
    pgid = int(os.environ.get("PGID", "1000"))
    return puid, pgid

def ensure_dir(path, uid, gid):
    # Create dir if missing
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            os.chown(path, uid, gid)
            return "CREATED"
        except Exception as e:
            return f"ERROR: Create failed: {e}"
    # Set ownership
    try:
        os.chown(path, uid, gid)
        # Fix perms for subfiles/dirs (non-recursive for speed)
        for root, dirs, files in os.walk(path):
            for d in dirs:
                try:
                    os.chown(os.path.join(root, d), uid, gid)
                except Exception:
                    pass
            for f in files:
                try:
                    os.chown(os.path.join(root, f), uid, gid)
                except Exception:
                    pass
            break  # Only one level deep
        # Verify
        stat = os.stat(path)
        if stat.st_uid == uid and stat.st_gid == gid:
            return "OK"
        else:
            return f"ERROR: Chown mismatch (got {stat.st_uid}:{stat.st_gid})"
    except Exception as e:
        return f"ERROR: Chown failed: {e}"

def main():
    puid, pgid = parse_uid_gid()
    uname = (
        pwd.getpwuid(puid).pw_name
        if puid in [u.pw_uid for u in pwd.getpwall()]
        else str(puid)
    )
    gname = (
        grp.getgrgid(pgid).gr_name
        if pgid in [g.gr_gid for g in grp.getgrall()]
        else str(pgid)
    )
    log(
        f"🔑 [volume-init] Target ownership: {puid}:{pgid} ({uname}:{gname})\n"
    )
    table = []
    error_count = 0
    for path in DIRS:
        status = ensure_dir(path, puid, pgid)
        table.append((path, status))
        if status.startswith("ERROR"):
            error_count += 1
    log("\n📝 Summary:")
    for path, status in table:
        log(f"  {path:20s} - {status}")
    if error_count:
        log(
            f"\n❌ [volume-init] {error_count} errors encountered. Please check logs above."
        )
        sys.exit(1)
    log("\n✅ [volume-init] All volumes checked and fixed where necessary.")

if __name__ == "__main__":
    main()
