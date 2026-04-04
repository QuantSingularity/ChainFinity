-- ChainFinity Database Initialization
-- Run once at container creation

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Set default search path
ALTER DATABASE chainfinity SET search_path TO public;

-- Create audit schema
CREATE SCHEMA IF NOT EXISTS audit;

-- Revoke public schema creation from public role
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

GRANT USAGE ON SCHEMA public TO chainfinity;
GRANT CREATE ON SCHEMA public TO chainfinity;
