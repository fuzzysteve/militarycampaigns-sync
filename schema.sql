-- Schema for the `militarycampaigns` database written to by run.py.
-- run.py does not create tables; apply this once before the first run:
--   mysql militarycampaigns < schema.sql
-- Safe to re-run (IF NOT EXISTS). Matches the live tables as of 2026-11-10.
--
-- IDs are stored dashless (char(32)) via SQLAlchemy's Uuid type; ESI wants
-- them dashed. run.py also reads campaign IDs from eve.milCampaigns (the
-- shared SDE import), which is not part of this schema.

-- One row per campaign, from GET /military-campaigns.
-- state: Unspecified / Active / Completed / Expired.
-- progress is capped by ESI at the campaign's targetProgress.
-- finished: when the campaign left Active (for Completed, when it hit its
-- target - can be well before the season's objectives expire).
CREATE TABLE IF NOT EXISTS `milCampaignStatus` (
  `campaignID` char(32) NOT NULL,
  `state` varchar(20) NOT NULL,
  `progress` bigint(20) NOT NULL,
  `started` datetime DEFAULT NULL,
  `finished` datetime DEFAULT NULL,
  `fetchedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`campaignID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- One row per objective, from GET /military-campaigns/{campaign_id}/objectives.
CREATE TABLE IF NOT EXISTS `milCampaignObjectiveStatus` (
  `objectiveID` char(32) NOT NULL,
  `campaignID` char(32) NOT NULL,
  `state` varchar(20) NOT NULL,
  `progress` bigint(20) NOT NULL,
  `participantsTotal` int(11) DEFAULT NULL,
  `participantsCommitted` int(11) DEFAULT NULL,
  `participantsContributors` int(11) DEFAULT NULL,
  `started` datetime DEFAULT NULL,
  `finished` datetime DEFAULT NULL,
  `lastModified` datetime DEFAULT NULL,
  `fetchedAt` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`objectiveID`),
  KEY `campaignID` (`campaignID`),
  KEY `state` (`state`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Per-campaign `after` cursor for the objectives feed (see CLAUDE.md).
-- Deleting a campaign's row makes the next run do a full walk from after=0.
CREATE TABLE IF NOT EXISTS `milCampaignSyncCursor` (
  `campaignID` char(32) NOT NULL,
  `afterCursor` varchar(255) NOT NULL,
  PRIMARY KEY (`campaignID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
