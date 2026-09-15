-- Sistema de Seguimiento de Combustibles. Solo datos sinteticos/de prueba.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE user_role AS ENUM ('ADMIN', 'OPERATOR', 'SUPERVISOR');
CREATE TYPE case_status AS ENUM ('PENDING', 'IN_REVIEW', 'RESOLVED', 'DISMISSED');

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role user_role NOT NULL DEFAULT 'OPERATOR',
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE stations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code VARCHAR(30) NOT NULL UNIQUE,
  name VARCHAR(150) NOT NULL,
  municipality VARCHAR(100) NOT NULL DEFAULT 'La Paz',
  address VARCHAR(255),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE vehicles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  plate VARCHAR(15) NOT NULL UNIQUE,
  vehicle_type VARCHAR(60),
  internal_code VARCHAR(50),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE fuel_types (
  id SMALLSERIAL PRIMARY KEY,
  code VARCHAR(20) NOT NULL UNIQUE,
  name VARCHAR(80) NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE tracking_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code VARCHAR(40) NOT NULL UNIQUE,
  name VARCHAR(120) NOT NULL,
  description TEXT NOT NULL,
  threshold NUMERIC(12,2) NOT NULL,
  window_hours INTEGER NOT NULL DEFAULT 24 CHECK (window_hours > 0),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE fuel_operations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vehicle_id UUID NOT NULL REFERENCES vehicles(id),
  station_id UUID NOT NULL REFERENCES stations(id),
  fuel_type_id SMALLINT NOT NULL REFERENCES fuel_types(id),
  quantity_liters NUMERIC(10,2) NOT NULL CHECK (quantity_liters > 0),
  occurred_at TIMESTAMPTZ NOT NULL,
  registered_by UUID REFERENCES users(id),
  notes VARCHAR(500),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE review_cases (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vehicle_id UUID NOT NULL REFERENCES vehicles(id),
  operation_id UUID REFERENCES fuel_operations(id),
  status case_status NOT NULL DEFAULT 'PENDING',
  assigned_to UUID REFERENCES users(id),
  conclusion TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE case_reasons (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id UUID NOT NULL REFERENCES review_cases(id) ON DELETE CASCADE,
  rule_id UUID REFERENCES tracking_rules(id),
  reason TEXT NOT NULL,
  observed_value NUMERIC(12,2),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_operations_vehicle_time ON fuel_operations(vehicle_id, occurred_at DESC);
CREATE INDEX idx_operations_station_time ON fuel_operations(station_id, occurred_at DESC);
CREATE INDEX idx_cases_status ON review_cases(status);

INSERT INTO fuel_types (code, name) VALUES
  ('GAS_ESP', 'Gasolina Especial'), ('DIESEL', 'Diesel Oil')
ON CONFLICT (code) DO NOTHING;

INSERT INTO tracking_rules (code, name, description, threshold, window_hours) VALUES
  ('HIGH_VOLUME', 'Volumen elevado', 'Cantidad por operación superior al límite establecido.', 120, 24),
  ('SHORT_INTERVAL', 'Carguíos frecuentes', 'Dos carguíos del mismo vehículo dentro de un periodo corto.', 2, 4),
  ('MULTI_STATION', 'Múltiples estaciones', 'Uso de varias estaciones por el mismo vehículo en una ventana de tiempo.', 2, 24)
ON CONFLICT (code) DO NOTHING;
