CREATE TABLE IF NOT EXISTS sdr (id INTEGER AUTO_INCREMENT, id_module INTEGER, frq_start INTEGER, frq_end INTEGER, threshold INTEGER)
CREATE TABLE IF NOT EXISTS module (id INTEGER, last_config DATETIME, last_ping DATETIME, gps_lat REAL, gps_lng REAL)
CREATE TABLE IF NOT EXISTS detection (id INTEGER AUTO_INCREMENT, id_module INTEGER, gdh DATETIME, frq INTEGER)