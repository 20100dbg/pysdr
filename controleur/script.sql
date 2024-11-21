CREATE TABLE IF NOT EXISTS module (
    id INTEGER, 
    last_config REAL, 
    last_ping REAL,
    frq_start INTEGER, 
    frq_end INTEGER, 
    threshold INTEGER);

CREATE TABLE IF NOT EXISTS detection (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    id_module INTEGER, 
    gdh REAL, 
    frq INTEGER);