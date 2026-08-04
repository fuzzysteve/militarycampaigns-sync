# militarycampaigns-sync

Pulls current state/progress for every military campaign objective from EVE
Online's ESI API and upserts it into the `militarycampaigns.milCampaignObjectiveStatus`
table.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- MySQL databases:
  - `eve` — must already contain a populated `milCampaigns` table (list of
    campaign IDs to sync)
  - `militarycampaigns` — destination for `milCampaignObjectiveStatus`

## Setup

```bash
uv sync
cp config.example.py config.py
```

Edit `config.py` with your real `EVE_DB_URL` / `STATUS_DB_URL` connection
strings. `config.py` is gitignored since it holds credentials — never commit
it.

## Running manually

```bash
uv run run.py
```

or, using the synced virtualenv directly:

```bash
.venv/bin/python3 run.py
```

## Running on a schedule

Unit files in [`systemd/`](systemd/) run the sync hourly at :45 past the
hour via systemd. To install:

```bash
sudo cp systemd/militarycampaigns-sync.service systemd/militarycampaigns-sync.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now militarycampaigns-sync.timer
```

Check status/logs with:

```bash
systemctl list-timers militarycampaigns-sync.timer
journalctl -u militarycampaigns-sync.service
```
