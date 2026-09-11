-- M1 track metadata is private to the Python backend and is not exposed through
-- Supabase's browser-facing Data API.
CREATE SCHEMA IF NOT EXISTS private;
REVOKE ALL ON SCHEMA private FROM PUBLIC;

CREATE TABLE private.tracks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id text NOT NULL,
    title text NOT NULL,
    duration_seconds double precision NOT NULL
        CHECK (
            duration_seconds > 0
            AND duration_seconds < 'Infinity'::double precision
        ),
    created_at timestamp with time zone NOT NULL DEFAULT now()
);

CREATE INDEX tracks_owner_created_at_id_idx
    ON private.tracks (owner_id, created_at DESC, id DESC);

DO $migration$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'audio_backend') THEN
        CREATE ROLE audio_backend NOLOGIN;
    END IF;
END
$migration$;

GRANT audio_backend TO CURRENT_USER;
GRANT USAGE ON SCHEMA private TO audio_backend;
GRANT SELECT ON TABLE private.tracks TO audio_backend;
