# militarycampaigns-sync

Pulls current state/progress for every military campaign, and every campaign
objective, from EVE Online's ESI API and upserts them into the
`militarycampaigns.milCampaignStatus` and
`militarycampaigns.milCampaignObjectiveStatus` tables.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- MySQL databases:
  - `eve` — must already contain a populated `milCampaigns` table (list of
    campaign IDs to sync)
  - `militarycampaigns` — destination for `milCampaignStatus`,
    `milCampaignObjectiveStatus` and `milCampaignSyncCursor` (created from
    [`schema.sql`](schema.sql))

## Setup

```bash
uv sync
cp config.example.py config.py
mysql militarycampaigns < schema.sql
```

`run.py` doesn't create its tables. `schema.sql` uses `CREATE TABLE IF NOT
EXISTS`, so it's safe to re-run.

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

## Cursor pagination

The objectives endpoint takes `after`/`before` cursors, and they don't behave
symmetrically:

- Omitting `after` (or passing a non-zero value that isn't a real prior
  cursor) starts you at the *end* of the feed, and you'd have to page
  backwards with `before` to walk the rest of it.
- Passing `after=0` starts you at the *beginning* of the feed, and you page
  forwards with each response's `cursor.after`.
- Passing a real `after` value returned from a previous run gets you only
  objectives updated since that point — i.e. it doubles as a "what's changed
  since last sync" cursor, not just a pagination offset.

So the sync does a full forward walk from `after=0` on the very first run
for a campaign, then persists the `after` cursor from the last (incomplete)
page it saw into `milCampaignSyncCursor`. Every subsequent run resumes from
that stored cursor, so it only pulls objectives that changed since the last
sync instead of re-walking the whole feed every hour.

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
