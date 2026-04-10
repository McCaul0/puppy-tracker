# Puppy Coordinator

A self hosted puppy activity tracker for two phones on the same home network.

## Documentation

The current behavioral source of truth is [`puppy_coordinator_behavioral_spec_v14.md`](C:\Users\mccau\Codex Projects\puppy_tracker\puppy_coordinator_behavioral_spec_v14.md).

The in-progress release candidate and supporting process docs live under [`test_app`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app), with the docs index at [`test_app/docs/README.md`](C:\Users\mccau\Codex Projects\puppy_tracker\test_app\docs\README.md).

This root README is mainly for running and deploying the current live app.

## What It Does

- Shared live activity log
- Tracks potty, food, water, sleep, play, wake events, and notes
- Shows how long since each key activity
- Updates in real time across open phones with WebSockets
- Stores everything locally in SQLite on your server
- Lets you rename activities, household members, and the puppy

## Good Default Assumptions Used For v1

- Only your household uses it
- It runs on your LAN, not exposed to the public internet
- You want the fastest possible version first, not a full account system
- Real time matters more than heavy reporting
- You want something phone friendly and dead simple

## Run It

1. Install Python 3.11 or newer.
2. In this folder:

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# or on Windows PowerShell:
# .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

3. Open it from devices on your network:

```text
http://YOUR-SERVER-IP:8000
```

Example:

```text
http://192.168.1.50:8000
```

## Optional Environment Variables

```bash
PUPPY_TRACKER_PORT=8000
PUPPY_TRACKER_DB=puppy_tracker.db
PUPPY_TZ_OFFSET_MINUTES=-240
```

## Recommended Home Deployment

- Put it on a small always-on machine like a mini PC, NAS app host, or Raspberry Pi
- Give that machine a static DHCP reservation in your router
- Keep it LAN only unless you add proper auth and HTTPS

## Easy Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py ./
EXPOSE 8000
CMD ["python", "app.py"]
```

```bash
docker build -t puppy-coordinator .
docker run -d --name puppy-coordinator -p 8000:8000 -v $(pwd):/app puppy-coordinator
```

## Next Upgrades Worth Doing

- PIN or password auth
- Push notifications when potty is due
- Filter by day and export history
- Visible and adjustable expected schedule profile by puppy age
- Safer release and migration workflow
- Roles and activity audit history

## Docker

### Fastest Option With Docker Compose

From this folder:

```bash
docker compose up -d --build
```

Then open:

```text
http://YOUR-SERVER-IP:8000
```

Your SQLite database will persist in:

```text
./data/puppy_tracker.db
```

Stop it:

```bash
docker compose down
```

See logs:

```bash
docker compose logs -f
```

### Plain Docker

Build it:

```bash
docker build -t puppy-coordinator .
```

Run it:

```bash
docker run -d \
  --name puppy-coordinator \
  -p 8000:8000 \
  -e PUPPY_TRACKER_PORT=8000 \
  -e PUPPY_TRACKER_DB=/data/puppy_tracker.db \
  -e PUPPY_TZ_OFFSET_MINUTES=-240 \
  -v $(pwd)/data:/data \
  --restart unless-stopped \
  puppy-coordinator
```

On Windows PowerShell:

```powershell
docker run -d `
  --name puppy-coordinator `
  -p 8000:8000 `
  -e PUPPY_TRACKER_PORT=8000 `
  -e PUPPY_TRACKER_DB=/data/puppy_tracker.db `
  -e PUPPY_TZ_OFFSET_MINUTES=-240 `
  -v ${PWD}/data:/data `
  --restart unless-stopped `
  puppy-coordinator
```

### Notes For Home Network Use

- Give the host machine a DHCP reservation so the IP does not change
- Keep this LAN only unless you add auth and HTTPS
- If Docker is running on a NAS or mini PC, the same compose file should work with very little change
