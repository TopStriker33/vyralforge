-- Vyral Forge SQLite schema

CREATE TABLE IF NOT EXISTS posts (
    id              TEXT PRIMARY KEY,         -- IG shortcode
    niche           TEXT NOT NULL,
    type            TEXT NOT NULL,            -- 'reel' | 'post' | 'carousel'
    owner_username  TEXT,
    owner_followers INTEGER,
    caption         TEXT,
    transcript      TEXT,
    audio_id        TEXT,
    audio_title     TEXT,
    audio_artist    TEXT,
    posted_at       TIMESTAMP,
    play_count      INTEGER,
    like_count      INTEGER,
    comment_count   INTEGER,
    share_count     INTEGER,                  -- often NULL
    view_count      INTEGER,                  -- often NULL since IG removed counter
    hashtags        TEXT,                     -- JSON array
    url             TEXT,
    video_duration  REAL,
    viral_score     REAL,                     -- computed
    scraped_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_posts_niche ON posts(niche);
CREATE INDEX IF NOT EXISTS idx_posts_score ON posts(viral_score DESC);
CREATE INDEX IF NOT EXISTS idx_posts_audio ON posts(audio_id);
CREATE INDEX IF NOT EXISTS idx_posts_posted ON posts(posted_at DESC);

CREATE TABLE IF NOT EXISTS sounds (
    audio_id        TEXT PRIMARY KEY,
    title           TEXT,
    artist          TEXT,
    first_seen      TIMESTAMP,
    last_seen       TIMESTAMP,
    usage_count     INTEGER DEFAULT 0,
    avg_play_count  REAL,
    lifecycle       TEXT,                     -- 'rising' | 'peak' | 'dying' | 'dead'
    source          TEXT,                     -- 'instagram' | 'tiktok'
    tiktok_first_seen TIMESTAMP               -- for cross-platform trend radar
);

CREATE INDEX IF NOT EXISTS idx_sounds_lifecycle ON sounds(lifecycle);

CREATE TABLE IF NOT EXISTS hooks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    niche           TEXT NOT NULL,
    formula         TEXT NOT NULL,            -- e.g. "POV first-person"
    example         TEXT,
    avg_score       REAL,
    sample_post_id  TEXT,
    extracted_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS timing_heatmap (
    niche           TEXT NOT NULL,
    day_of_week     INTEGER NOT NULL,         -- 0=Mon, 6=Sun
    hour_of_day     INTEGER NOT NULL,         -- 0-23, local time
    sample_size     INTEGER,
    avg_score       REAL,
    PRIMARY KEY (niche, day_of_week, hour_of_day)
);

CREATE TABLE IF NOT EXISTS plans (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    niche           TEXT NOT NULL,
    week_start      DATE NOT NULL,
    theme           TEXT,
    plan_json       TEXT NOT NULL,            -- 7-day plan
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
