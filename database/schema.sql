CREATE TABLE IF NOT EXISTS vehicles (
    id SERIAL PRIMARY KEY,
    plate_number VARCHAR(20) UNIQUE NOT NULL,
    vehicle_type VARCHAR(50) DEFAULT 'two_wheeler',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS violations (
    id SERIAL PRIMARY KEY,
    violation_id VARCHAR(50) UNIQUE NOT NULL,
    vehicle_id INTEGER REFERENCES vehicles(id),
    violation_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    location VARCHAR(200),
    confidence FLOAT DEFAULT 0.0,
    fine_amount INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    plate_number VARCHAR(20),
    track_id INTEGER,
    camera_id VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS evidence (
    id SERIAL PRIMARY KEY,
    violation_id INTEGER REFERENCES violations(id) NOT NULL,
    image_path VARCHAR(500),
    video_timestamp VARCHAR(50),
    full_frame_path VARCHAR(500),
    vehicle_crop_path VARCHAR(500),
    plate_crop_path VARCHAR(500),
    metadata_json JSONB
);

CREATE TABLE IF NOT EXISTS cameras (
    id SERIAL PRIMARY KEY,
    camera_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100),
    location VARCHAR(200),
    configuration JSONB DEFAULT '{}',
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS violation_rules (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) UNIQUE NOT NULL,
    fine_amount INTEGER DEFAULT 1000,
    active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_violations_type ON violations(violation_type);
CREATE INDEX IF NOT EXISTS idx_violations_timestamp ON violations(timestamp);
CREATE INDEX IF NOT EXISTS idx_violations_plate ON violations(plate_number);
CREATE INDEX IF NOT EXISTS idx_violations_status ON violations(status);
