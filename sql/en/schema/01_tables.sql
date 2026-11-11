-- =====================================================================
-- "Montreal Rents" database: star schema
-- Engine: SQLite (PostgreSQL / DuckDB compatible with minor changes)
-- The grain of each fact table is given in a comment.
-- =====================================================================
PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------- dimensions
CREATE TABLE dim_unit_type (
  unit_id   TEXT    PRIMARY KEY,                       -- studio, 1br, 2br, 3br
  label_fr  TEXT    NOT NULL UNIQUE,
  label_en  TEXT    NOT NULL,
  bedrooms  INTEGER NOT NULL CHECK (bedrooms BETWEEN 0 AND 3)
);

CREATE TABLE dim_city (                                   -- six large metro areas (CMHC annual series)
  geo_id    TEXT PRIMARY KEY,
  label_fr  TEXT NOT NULL,
  label_en  TEXT NOT NULL
);

CREATE TABLE dim_province (                              -- 10 provinces, 3 territories and Canada (aggregate)
  code   TEXT PRIMARY KEY CHECK (length(code) = 2),
  name   TEXT NOT NULL UNIQUE,
  level  TEXT NOT NULL CHECK (level IN ('province', 'territory', 'country'))
);

CREATE TABLE dim_estimate (                            -- type of estimate in table 46-10-0092
  code   TEXT PRIMARY KEY CHECK (code IN ('A', 'P')),
  label  TEXT NOT NULL UNIQUE                       -- A = asking rent, P = rent paid
);

CREATE TABLE dim_indicator (                            -- indicators from the CMHC report; the unit depends on the indicator alone (3NF)
  code   TEXT PRIMARY KEY,
  label  TEXT NOT NULL,
  unit   TEXT NOT NULL CHECK (unit IN ('dollars', 'pct'))
);

CREATE TABLE dim_metro_area (                                   -- 42 metro areas of table 46-10-0092 (+ all areas)
  geo_id    INTEGER PRIMARY KEY,
  name      TEXT    NOT NULL,
  province  TEXT    NOT NULL REFERENCES dim_province (code),
  lat       REAL    CHECK (lat IS NULL OR lat BETWEEN 41 AND 84),
  lon       REAL    CHECK (lon IS NULL OR lon BETWEEN -142 AND -52)
);

-- ---------------------------------------------------------------- facts
-- Grain: one year × one metro area × one unit type (October average rent, current dollars)
CREATE TABLE fact_rent (
  year     INTEGER NOT NULL CHECK (year BETWEEN 1987 AND 2100),
  geo_id   TEXT    NOT NULL REFERENCES dim_city (geo_id),
  unit_id  TEXT    NOT NULL REFERENCES dim_unit_type (unit_id),
  rent     INTEGER NOT NULL CHECK (rent > 0),
  PRIMARY KEY (year, geo_id, unit_id)
);

-- Grain: one year × one metro area (vacancy rate, buildings with 6 units or more, %)
CREATE TABLE fact_vacancy (
  year    INTEGER NOT NULL,
  geo_id  TEXT    NOT NULL REFERENCES dim_city (geo_id),
  rate    REAL    NOT NULL CHECK (rate BETWEEN 0 AND 100),
  PRIMARY KEY (year, geo_id)
);

-- Grain: one quarter × one metro area × one estimate (A = asking rent, P = rent paid), two-bedroom
CREATE TABLE fact_rent_quarterly (
  period    TEXT    NOT NULL CHECK (period GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]'),
  geo_id    INTEGER NOT NULL REFERENCES dim_metro_area (geo_id),
  estimate  TEXT    NOT NULL REFERENCES dim_estimate (code),
  rent      REAL    CHECK (rent IS NULL OR rent > 0),  -- NULL = not published by Statistics Canada
  grade     TEXT    CHECK (grade IS NULL OR grade IN ('E', 'F', '..')),
  PRIMARY KEY (period, geo_id, estimate)
);

-- Grain: one year × one large city (all-items CPI, annual average, 2002 = 100; Montreal)
CREATE TABLE cpi (
  year    INTEGER NOT NULL,
  geo_id  TEXT    NOT NULL REFERENCES dim_city (geo_id),
  cpi     REAL    NOT NULL CHECK (cpi > 0),
  PRIMARY KEY (year, geo_id)
);

-- Grain: one year × one province (rent CPI and all-items CPI, 2002 = 100)
CREATE TABLE cpi_provinces (
  year           INTEGER NOT NULL,
  code           TEXT    NOT NULL REFERENCES dim_province (code),
  rent_cpi       REAL    NOT NULL CHECK (rent_cpi > 0),
  all_items_cpi  REAL    NOT NULL CHECK (all_items_cpi > 0),
  PRIMARY KEY (year, code)
);

-- Grain: one year × one large city × one indicator published in the 2025 CMHC report
CREATE TABLE cmhc_turnover (
  year       INTEGER NOT NULL,
  geo_id     TEXT    NOT NULL REFERENCES dim_city (geo_id),
  indicator  TEXT    NOT NULL REFERENCES dim_indicator (code),
  value      REAL    NOT NULL,
  PRIMARY KEY (year, geo_id, indicator)
);

-- ---------------------------------------------------------------- index
CREATE INDEX ix_rent_geo_unit     ON fact_rent (geo_id, unit_id, year);
CREATE INDEX ix_quarter_geo_est       ON fact_rent_quarterly (geo_id, estimate, period);
CREATE INDEX ix_metro_province       ON dim_metro_area (province);
CREATE INDEX ix_cpip_code          ON cpi_provinces (code, year);
