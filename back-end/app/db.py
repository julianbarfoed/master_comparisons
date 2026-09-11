"""Supabase Postgres persistence for track metadata."""

from collections.abc import Callable
from typing import Any

import psycopg

from app.tracks import Track, TrackRepositoryUnavailable

Connect = Callable[..., psycopg.Connection[Any]]


class PostgresTrackRepository:
    """Read owner-scoped track metadata through a restricted database role."""

    def __init__(
        self,
        database_url: str,
        *,
        connect: Connect = psycopg.connect,
        connect_timeout_seconds: int = 5,
    ) -> None:
        if not database_url.strip():
            raise ValueError("database URL must not be blank")

        self._database_url = database_url
        self._connect = connect
        self._connect_timeout_seconds = connect_timeout_seconds

    def list_tracks(self, user_id: str) -> list[Track]:
        try:
            with self._connect(
                self._database_url,
                connect_timeout=self._connect_timeout_seconds,
            ) as connection, connection.cursor() as cursor:
                cursor.execute("SET LOCAL ROLE audio_backend")
                cursor.execute(
                    """
                    SELECT id::text, owner_id, title, duration_seconds, created_at
                    FROM private.tracks
                    WHERE owner_id = %s
                    ORDER BY created_at DESC, id DESC
                    """,
                    (user_id,),
                )
                return [
                    Track(
                        id=row[0],
                        owner_id=row[1],
                        title=row[2],
                        duration_seconds=row[3],
                        created_at=row[4],
                    )
                    for row in cursor.fetchall()
                ]
        except psycopg.Error as error:
            raise TrackRepositoryUnavailable("track metadata query failed") from error
