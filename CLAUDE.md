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
