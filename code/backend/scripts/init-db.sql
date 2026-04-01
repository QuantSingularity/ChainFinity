-- ChainFinity Database Initialization Script
-- Creates required extensions and initial configuration

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'UTC';

-- Create application role with limited privileges
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'chainfinity_app') THEN
        CREATE ROLE chainfinity_app LOGIN PASSWORD 'changeme_in_production';
    END IF;
END $$;

GRANT CONNECT ON DATABASE chainfinity TO chainfinity_app;
GRANT USAGE ON SCHEMA public TO chainfinity_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO chainfinity_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO chainfinity_app;
