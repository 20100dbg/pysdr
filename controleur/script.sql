CREATE TABLE IF NOT EXISTS module (
    id INTEGER, 
    frq_start INTEGER, 
    frq_end INTEGER,
    threshold INTEGER,
    latitude REAL,
    longitude REAL,
    last_config DATETIME, 
    last_ping DATETIME,
    config_applied BOOLEAN
    );

CREATE TABLE IF NOT EXISTS detection (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    module_id INTEGER, 
    dt DATETIME,
    frq INTEGER);