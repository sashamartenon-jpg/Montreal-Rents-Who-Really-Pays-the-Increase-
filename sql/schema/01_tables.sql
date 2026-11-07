-- =====================================================================
-- Base de données « Loyers à Montréal » : modèle en étoile
-- Moteur : SQLite (compatible PostgreSQL / DuckDB avec ajustements mineurs)
-- Grain de chaque table de faits indiqué en commentaire.
-- =====================================================================
PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------- dimensions
CREATE TABLE dim_logement (
  unit_id     TEXT    PRIMARY KEY,                       -- studio, 1ch, 2ch, 3ch
  libelle_fr  TEXT    NOT NULL UNIQUE,
  libelle_en  TEXT    NOT NULL,
  chambres    INTEGER NOT NULL CHECK (chambres BETWEEN 0 AND 3)
);

CREATE TABLE dim_geo (                                   -- six grandes RMR (séries annuelles SCHL)
  geo_id      TEXT PRIMARY KEY,
  libelle_fr  TEXT NOT NULL,
  libelle_en  TEXT NOT NULL
);

CREATE TABLE dim_province (                              -- 10 provinces, 3 territoires et le Canada (agrégat)
  code        TEXT PRIMARY KEY CHECK (length(code) = 2),
  nom         TEXT NOT NULL UNIQUE,
  niveau      TEXT NOT NULL CHECK (niveau IN ('province', 'territoire', 'pays'))
);

CREATE TABLE dim_estimation (                            -- type d'estimation du tableau 46-10-0092
  code        TEXT PRIMARY KEY CHECK (code IN ('A', 'P')),
  libelle     TEXT NOT NULL UNIQUE                       -- A = loyer demandé, P = loyer payé
);

CREATE TABLE dim_indicateur (                            -- indicateurs du rapport SCHL ; l'unité dépend de l'indicateur seul (3FN)
  code        TEXT PRIMARY KEY,
  libelle     TEXT NOT NULL,
  unite       TEXT NOT NULL CHECK (unite IN ('dollars', 'pct'))
);

CREATE TABLE dim_rmr (                                   -- 42 RMR du tableau 46-10-0092 (+ ensemble)
  geo_id      INTEGER PRIMARY KEY,
  nom         TEXT    NOT NULL,
  province    TEXT    NOT NULL REFERENCES dim_province (code),
  lat         REAL    CHECK (lat IS NULL OR lat BETWEEN 41 AND 84),
  lon         REAL    CHECK (lon IS NULL OR lon BETWEEN -142 AND -52)
);

-- ---------------------------------------------------------------- faits
-- Grain : une année × une RMR × un type de logement (loyer moyen d'octobre, $ courants)
CREATE TABLE fait_loyer (
  annee    INTEGER NOT NULL CHECK (annee BETWEEN 1987 AND 2100),
  geo_id   TEXT    NOT NULL REFERENCES dim_geo (geo_id),
  unit_id  TEXT    NOT NULL REFERENCES dim_logement (unit_id),
  loyer    INTEGER NOT NULL CHECK (loyer > 0),
  PRIMARY KEY (annee, geo_id, unit_id)
);

-- Grain : une année × une RMR (taux d'inoccupation, immeubles de 6 logements et plus, %)
CREATE TABLE fait_inoccupation (
  annee   INTEGER NOT NULL,
  geo_id  TEXT    NOT NULL REFERENCES dim_geo (geo_id),
  taux    REAL    NOT NULL CHECK (taux BETWEEN 0 AND 100),
  PRIMARY KEY (annee, geo_id)
);

-- Grain : un trimestre × une RMR × une estimation (A = loyer demandé, P = loyer payé), 2 chambres
CREATE TABLE fait_loyer_trimestriel (
  periode     TEXT    NOT NULL CHECK (periode GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]'),
  geo_id      INTEGER NOT NULL REFERENCES dim_rmr (geo_id),
  estimation  TEXT    NOT NULL REFERENCES dim_estimation (code),
  loyer       REAL    CHECK (loyer IS NULL OR loyer > 0),  -- NULL = non publié par Statistique Canada
  cote        TEXT    CHECK (cote IS NULL OR cote IN ('E', 'F', '..')),
  PRIMARY KEY (periode, geo_id, estimation)
);

-- Grain : une année × une grande ville (IPC d'ensemble, moyenne annuelle, 2002 = 100 ; Montréal)
CREATE TABLE ipc (
  annee   INTEGER NOT NULL,
  geo_id  TEXT    NOT NULL REFERENCES dim_geo (geo_id),
  ipc     REAL    NOT NULL CHECK (ipc > 0),
  PRIMARY KEY (annee, geo_id)
);

-- Grain : une année × une province (IPC du loyer et IPC d'ensemble, 2002 = 100)
CREATE TABLE ipc_provinces (
  annee         INTEGER NOT NULL,
  code          TEXT    NOT NULL REFERENCES dim_province (code),
  ipc_loyer     REAL    NOT NULL CHECK (ipc_loyer > 0),
  ipc_ensemble  REAL    NOT NULL CHECK (ipc_ensemble > 0),
  PRIMARY KEY (annee, code)
);

-- Grain : une année × une grande ville × un indicateur publié dans le rapport SCHL 2025
CREATE TABLE schl_roulement (
  annee       INTEGER NOT NULL,
  geo_id      TEXT    NOT NULL REFERENCES dim_geo (geo_id),
  indicateur  TEXT    NOT NULL REFERENCES dim_indicateur (code),
  valeur      REAL    NOT NULL,
  PRIMARY KEY (annee, geo_id, indicateur)
);

-- ---------------------------------------------------------------- index
CREATE INDEX ix_loyer_geo_unit     ON fait_loyer (geo_id, unit_id, annee);
CREATE INDEX ix_trim_geo_est       ON fait_loyer_trimestriel (geo_id, estimation, periode);
CREATE INDEX ix_rmr_province       ON dim_rmr (province);
CREATE INDEX ix_ipcp_code          ON ipc_provinces (code, annee);
