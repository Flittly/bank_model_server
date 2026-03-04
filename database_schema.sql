-- ========================================
-- Bank workflow schema (PostgreSQL + PostGIS)
-- ========================================

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS bank_segments (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL,
    segment_id VARCHAR(100) UNIQUE NOT NULL,
    segment_name VARCHAR(100) NOT NULL,
    region_code VARCHAR(50) NOT NULL,
    start_point GEOMETRY(Point, 4326),
    end_point GEOMETRY(Point, 4326),
    geom GEOMETRY(LineString, 4326),
    dem_id VARCHAR(100),
    bench_id VARCHAR(100),
    ref_id VARCHAR(100),
    hydro_segment VARCHAR(50),
    hydro_year VARCHAR(20),
    hydro_set VARCHAR(50),
    protection_level VARCHAR(20),
    control_level VARCHAR(20),
    other_params JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_segments_case ON bank_segments(case_id);
CREATE INDEX IF NOT EXISTS idx_segments_region ON bank_segments(region_code);
CREATE INDEX IF NOT EXISTS idx_segments_geom ON bank_segments USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_segments_id ON bank_segments(segment_id);

CREATE OR REPLACE FUNCTION update_bank_segments_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS trigger_bank_segments_updated_at ON bank_segments;
CREATE TRIGGER trigger_bank_segments_updated_at
BEFORE UPDATE ON bank_segments
FOR EACH ROW EXECUTE FUNCTION update_bank_segments_updated_at();

CREATE TABLE IF NOT EXISTS cross_sections (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL,
    section_id VARCHAR(100) UNIQUE NOT NULL,
    section_name VARCHAR(100) NOT NULL,
    segment_id INTEGER NOT NULL,
    region_code VARCHAR(50) NOT NULL,
    segment_index INTEGER,
    start_point GEOMETRY(Point, 4326),
    end_point GEOMETRY(Point, 4326),
    geom GEOMETRY(LineString, 4326),
    hs NUMERIC,
    hc NUMERIC,
    protection_level VARCHAR(20),
    control_level VARCHAR(20),
    water_qs VARCHAR(20),
    tidal_level VARCHAR(20),
    current_timepoint DATE,
    comparison_timepoint DATE,
    risk_thresholds JSONB,
    weights JSONB,
    other_params JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (segment_id) REFERENCES bank_segments(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sections_case ON cross_sections(case_id);
CREATE INDEX IF NOT EXISTS idx_sections_segment ON cross_sections(segment_id);
CREATE INDEX IF NOT EXISTS idx_sections_region ON cross_sections(region_code);
CREATE INDEX IF NOT EXISTS idx_sections_geom ON cross_sections USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_sections_id ON cross_sections(section_id);

CREATE OR REPLACE FUNCTION update_cross_sections_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS trigger_cross_sections_updated_at ON cross_sections;
CREATE TRIGGER trigger_cross_sections_updated_at
BEFORE UPDATE ON cross_sections
FOR EACH ROW EXECUTE FUNCTION update_cross_sections_updated_at();

CREATE TABLE IF NOT EXISTS correction_lines (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL,
    correction_id VARCHAR(100) UNIQUE NOT NULL,
    geom GEOMETRY(LineString, 4326),
    correction_rules JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_correction_case ON correction_lines(case_id);
CREATE INDEX IF NOT EXISTS idx_correction_geom ON correction_lines USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_correction_id ON correction_lines(correction_id);

CREATE OR REPLACE FUNCTION update_correction_lines_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS trigger_correction_lines_updated_at ON correction_lines;
CREATE TRIGGER trigger_correction_lines_updated_at
BEFORE UPDATE ON correction_lines
FOR EACH ROW EXECUTE FUNCTION update_correction_lines_updated_at();

CREATE TABLE IF NOT EXISTS bank_risk_results (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(50) NOT NULL,
    section_id INTEGER NOT NULL,
    section_name VARCHAR(100),
    region_code VARCHAR(50),
    segment_id INTEGER,
    segment_name VARCHAR(100),
    run_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    risk_level INTEGER,
    indicators JSONB,
    geom GEOMETRY(LineString, 4326),
    FOREIGN KEY (section_id) REFERENCES cross_sections(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_bank_results_section ON bank_risk_results(section_id);
CREATE INDEX IF NOT EXISTS idx_bank_results_region ON bank_risk_results(region_code);
CREATE INDEX IF NOT EXISTS idx_bank_results_geom ON bank_risk_results USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_bank_results_case ON bank_risk_results(case_id);
