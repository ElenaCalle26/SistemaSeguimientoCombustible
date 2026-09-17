-- FuelTrack schema. All sample rows and B-SISA/RFID values are synthetic.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$ BEGIN
  CREATE TYPE user_role AS ENUM ('ADMIN', 'OPERATOR', 'SUPERVISOR');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN
  CREATE TYPE case_status AS ENUM ('PENDING', 'IN_REVIEW', 'RESOLVED', 'DISMISSED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS institutions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), code VARCHAR(30) UNIQUE NOT NULL,
  name VARCHAR(160) NOT NULL, is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS stations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), institution_id UUID NOT NULL REFERENCES institutions(id),
  code VARCHAR(30) UNIQUE NOT NULL, name VARCHAR(150) NOT NULL, municipality VARCHAR(100) NOT NULL DEFAULT 'La Paz',
  address VARCHAR(255), is_active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), institution_id UUID REFERENCES institutions(id),
  fixed_station_id UUID REFERENCES stations(id), full_name VARCHAR(120) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL, password_hash TEXT NOT NULL, role user_role NOT NULL DEFAULT 'OPERATOR',
  is_active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS user_station_assignments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  station_id UUID NOT NULL REFERENCES stations(id) ON DELETE CASCADE, is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  UNIQUE(user_id, station_id)
);
CREATE TABLE IF NOT EXISTS vehicles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), institution_id UUID NOT NULL REFERENCES institutions(id),
  plate VARCHAR(15) UNIQUE NOT NULL, vehicle_type VARCHAR(60), internal_code VARCHAR(50),
  b_sisa_code VARCHAR(40), synthetic_make_model VARCHAR(100), synthetic_year INTEGER,
  rfid_uid VARCHAR(80) UNIQUE, rfid_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS fuel_types (
  id SMALLSERIAL PRIMARY KEY, code VARCHAR(20) UNIQUE NOT NULL, name VARCHAR(80) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE TABLE IF NOT EXISTS station_fuel_authorizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), station_id UUID NOT NULL REFERENCES stations(id) ON DELETE CASCADE,
  fuel_type_id SMALLINT NOT NULL REFERENCES fuel_types(id) ON DELETE CASCADE, is_active BOOLEAN NOT NULL DEFAULT TRUE,
  UNIQUE(station_id, fuel_type_id)
);
CREATE TABLE IF NOT EXISTS tracking_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), code VARCHAR(40) UNIQUE NOT NULL, name VARCHAR(120) NOT NULL,
  description TEXT NOT NULL, threshold NUMERIC(12,2) NOT NULL, window_hours INTEGER NOT NULL CHECK(window_hours > 0),
  is_active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS fuel_operations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), institution_id UUID NOT NULL REFERENCES institutions(id),
  vehicle_id UUID NOT NULL REFERENCES vehicles(id), station_id UUID NOT NULL REFERENCES stations(id),
  fuel_type_id SMALLINT NOT NULL REFERENCES fuel_types(id), quantity_liters NUMERIC(10,2) NOT NULL CHECK(quantity_liters > 0),
  occurred_at TIMESTAMPTZ NOT NULL, registered_by UUID REFERENCES users(id), notes VARCHAR(500),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS review_cases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), institution_id UUID NOT NULL REFERENCES institutions(id),
  station_id UUID NOT NULL REFERENCES stations(id), vehicle_id UUID NOT NULL REFERENCES vehicles(id),
  operation_id UUID REFERENCES fuel_operations(id), status case_status NOT NULL DEFAULT 'PENDING',
  priority VARCHAR(15) NOT NULL DEFAULT 'NORMAL', assigned_to UUID REFERENCES users(id), conclusion TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS case_reasons (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), case_id UUID NOT NULL REFERENCES review_cases(id) ON DELETE CASCADE,
  rule_id UUID REFERENCES tracking_rules(id), reason TEXT NOT NULL, observed_value NUMERIC(12,2),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS case_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), case_id UUID NOT NULL REFERENCES review_cases(id) ON DELETE CASCADE,
  actor_id UUID NOT NULL REFERENCES users(id), action VARCHAR(40) NOT NULL, note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), institution_id UUID NOT NULL REFERENCES institutions(id),
  station_id UUID NOT NULL REFERENCES stations(id), vehicle_id UUID NOT NULL REFERENCES vehicles(id),
  operation_id UUID REFERENCES fuel_operations(id), case_id UUID REFERENCES review_cases(id),
  code VARCHAR(40) NOT NULL, severity VARCHAR(15) NOT NULL DEFAULT 'WARNING', message TEXT NOT NULL,
  is_read BOOLEAN NOT NULL DEFAULT FALSE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(), actor_id UUID REFERENCES users(id),
  institution_id UUID REFERENCES institutions(id), action VARCHAR(80) NOT NULL,
  entity_type VARCHAR(60) NOT NULL, entity_id VARCHAR(80), details TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_operations_vehicle_time ON fuel_operations(vehicle_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_operations_station_time ON fuel_operations(station_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_cases_status ON review_cases(status);
CREATE INDEX IF NOT EXISTS idx_alerts_station_time ON alerts(station_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_logs(created_at DESC);

-- Audit records are append-only, including for a database owner using the API role.
CREATE OR REPLACE FUNCTION prevent_audit_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'audit_logs is immutable'; END; $$;
DROP TRIGGER IF EXISTS audit_logs_immutable ON audit_logs;
CREATE TRIGGER audit_logs_immutable BEFORE UPDATE OR DELETE ON audit_logs
FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation();

INSERT INTO fuel_types(code,name) VALUES
 ('GAS_ESP','Gasolina Especial'), ('DIESEL','Diesel Oil'), ('GNV','Gas Natural Vehicular')
ON CONFLICT(code) DO NOTHING;
INSERT INTO tracking_rules(code,name,description,threshold,window_hours) VALUES
 ('HIGH_VOLUME','Volumen elevado','Cantidad superior a 120 litros.',120,24),
 ('SHORT_INTERVAL','Carguíos frecuentes','Carguíos dentro de cuatro horas.',1,4),
 ('MULTI_STATION','Entre estaciones','Uso de estaciones diferentes en 24 horas.',2,24),
 ('THIRD_FUELING','Tercer carguío prioritario','Tres o más carguíos en 24 horas.',3,24)
ON CONFLICT(code) DO NOTHING;

-- Synthetic institutions and stations. Password hashes are created by the API.
INSERT INTO institutions(code,name) VALUES
 ('INST-001','Cristo Autogas S.R.L.'),
 ('INST-002','Comercializadora Gas-May S.R.L.'),
 ('INST-003','Estación de Servicio Volcán S.R.L.')
ON CONFLICT(code) DO UPDATE SET name=EXCLUDED.name;
INSERT INTO stations(institution_id,code,name,municipality,address)
SELECT id,'EST-001','E/S Cristo Autogas S.R.L.','La Paz','Av. Chacaltaya N.° 804, zona Achachicala' FROM institutions WHERE code='INST-001'
ON CONFLICT(code) DO UPDATE SET name=EXCLUDED.name, institution_id=EXCLUDED.institution_id, address=EXCLUDED.address;
INSERT INTO stations(institution_id,code,name,municipality,address)
SELECT id,'EST-002','E/S Gas-May S.R.L.','La Paz','Av. General Juan José Torrez, en las inmediaciones del Cementerio La Llamita' FROM institutions WHERE code='INST-002'
ON CONFLICT(code) DO UPDATE SET name=EXCLUDED.name, institution_id=EXCLUDED.institution_id, address=EXCLUDED.address;
INSERT INTO stations(institution_id,code,name,municipality,address)
SELECT id,'EST-003','E/S Volcán S.R.L.','La Paz','Av. Montes esq. Pando N.° 101, Zona San Sebastián' FROM institutions WHERE code='INST-003'
ON CONFLICT(code) DO UPDATE SET name=EXCLUDED.name, institution_id=EXCLUDED.institution_id, address=EXCLUDED.address;
INSERT INTO station_fuel_authorizations(station_id,fuel_type_id)
SELECT s.id,f.id FROM stations s CROSS JOIN fuel_types f
WHERE s.code IN ('EST-001','EST-002','EST-003')
ON CONFLICT(station_id,fuel_type_id) DO NOTHING;
INSERT INTO vehicles(institution_id,plate,vehicle_type,internal_code,b_sisa_code,synthetic_make_model,synthetic_year,rfid_uid,rfid_enabled)
SELECT id,'SYN-001','Camioneta','DEMO-001','BSISA-SYN-001','Modelo Sintético A',2022,'RFID-DEMO-001',TRUE
FROM institutions WHERE code='INST-001' ON CONFLICT(plate) DO NOTHING;
INSERT INTO vehicles(institution_id,plate,vehicle_type,internal_code,b_sisa_code,synthetic_make_model,synthetic_year)
SELECT id,'SYN-002','Sedán','DEMO-002','BSISA-SYN-002','Modelo Sintético B',2023
FROM institutions WHERE code='INST-001' ON CONFLICT(plate) DO NOTHING;
