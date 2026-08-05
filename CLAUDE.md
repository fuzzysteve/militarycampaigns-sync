# militarycampaigns-sync

Single-script sync job: reads campaign IDs from the `eve.milCampaigns` table,
fetches each campaign's objectives from ESI
(`/military-campaigns/{campaign_id}/objectives`), and upserts them into
`militarycampaigns.milCampaignObjectiveStatus`. Entry point is `run.py`,
run via `uv run run.py`.

- DB connection strings live in `config.py`, which is gitignored — copy
  `config.example.py` to `config.py` and fill in real credentials locally.
  Never commit `config.py` or paste real credentials into source files.
- `systemd/` holds the unit files for the hourly (`:45` past the hour)
  scheduled run; keep them in sync with whatever's installed in
  `/etc/systemd/system/` if either changes.
- ESI's military-campaigns endpoint was previously behind an EVE SSO bearer
  token; that requirement has since been dropped and the endpoint is public,
  so `run.py` only sends `X-Compatibility-Date` now.
- The objectives endpoint's `after`/`before` cursors are asymmetric: no
  cursor (or a non-zero bogus one) lands you at the end of the feed and
  requires paging backwards with `before` to see everything, whereas
  `after=0` starts at the beginning and pages forward via `cursor.after`. A
  real `after` value from a prior response also acts as an incremental
  "changed since" filter, not just an offset. Because of that, `run.py`
  does a full forward walk from `after=0` only on a campaign's first sync,
  then persists the last page's `after` cursor in `milCampaignSyncCursor`
  and resumes from it on every later run — don't change this back to
  `before`-based paging from the end of the feed, since that was the
  original (buggy) approach and re-walks the whole feed every run instead
  of pulling just what changed.
