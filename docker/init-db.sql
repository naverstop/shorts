-- Initialize Database
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS public;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE shorts_db TO shorts_admin;
GRANT ALL PRIVILEGES ON SCHEMA public TO shorts_admin;

-- Set timezone
SET timezone = 'Asia/Seoul';

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed successfully!';
END $$;
