"""Pulls current state/progress for every military campaign objective from ESI
and upserts it into militarycampaigns.milCampaignObjectiveStatus.
"""

import sys
from datetime import datetime

import requests
from sqlalchemy import (
    BIGINT,
    INTEGER,
    VARCHAR,
    Column,
    DateTime,
    MetaData,
    Table,
    create_engine,
    select,
)
from sqlalchemy.dialects.mysql import insert as mysql_insert

from config import EVE_DB_URL, STATUS_DB_URL

ESI_LIMIT = 90

eve_metadata = MetaData()
milCampaigns = Table(
    'milCampaigns', eve_metadata,
    Column('campaignID', VARCHAR(length=36), primary_key=True),
)

status_metadata = MetaData()
milCampaignObjectiveStatus = Table(
    'milCampaignObjectiveStatus', status_metadata,
    Column('objectiveID', VARCHAR(length=36), primary_key=True),
    Column('campaignID', VARCHAR(length=36), nullable=False),
    Column('state', VARCHAR(length=20), nullable=False),
    Column('progress', BIGINT(), nullable=False),
    Column('participantsTotal', INTEGER()),
    Column('participantsCommitted', INTEGER()),
    Column('participantsContributors', INTEGER()),
    Column('started', DateTime()),
    Column('finished', DateTime()),
    Column('lastModified', DateTime()),
)


def esi_get(url):
    response = requests.get(url, headers={
        'Accept': 'application/json',
        'X-Compatibility-Date': '2026-08-04',
    }, timeout=30)
    response.raise_for_status()
    return response.json()


def to_datetime(iso_string):
    if not iso_string:
        return None
    return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))


def sync_campaign_objectives(connection, campaign_id):
    after = None
    count = 0

    while True:
        url = f'https://esi.evetech.net/military-campaigns/{campaign_id}/objectives?limit={ESI_LIMIT}'
        if after is not None:
            url += f'&after={after}'
        data = esi_get(url)

        objectives = data.get('objectives', [])
        for objective in objectives:
            participants = objective.get('participants', {})
            stmt = mysql_insert(milCampaignObjectiveStatus).values(
                objectiveID=objective['id'],
                campaignID=campaign_id,
                state=objective['state'],
                progress=objective['progress'],
                participantsTotal=participants.get('total'),
                participantsCommitted=participants.get('committed'),
                participantsContributors=participants.get('contributors'),
                started=to_datetime(objective.get('started')),
                finished=to_datetime(objective.get('finished')),
                lastModified=to_datetime(objective.get('last_modified')),
            )
            stmt = stmt.on_duplicate_key_update(
                campaignID=stmt.inserted.campaignID,
                state=stmt.inserted.state,
                progress=stmt.inserted.progress,
                participantsTotal=stmt.inserted.participantsTotal,
                participantsCommitted=stmt.inserted.participantsCommitted,
                participantsContributors=stmt.inserted.participantsContributors,
                started=stmt.inserted.started,
                finished=stmt.inserted.finished,
                lastModified=stmt.inserted.lastModified,
            )
            connection.execute(stmt)
            count += 1
        connection.commit()

        after = data.get('cursor', {}).get('after')
        if len(objectives) != ESI_LIMIT or after is None:
            break

    return count


def main():
    eve_engine = create_engine(EVE_DB_URL)
    status_engine = create_engine(STATUS_DB_URL)

    with eve_engine.connect() as eve_connection:
        campaign_ids = eve_connection.execute(select(milCampaigns.c.campaignID)).scalars().all()

    with status_engine.connect() as status_connection:
        for campaign_id in campaign_ids:
            try:
                count = sync_campaign_objectives(status_connection, campaign_id)
                print(f'{campaign_id}: {count} objectives synced')
            except Exception as e:
                print(f'{campaign_id}: FAILED - {e}', file=sys.stderr)


if __name__ == '__main__':
    main()
