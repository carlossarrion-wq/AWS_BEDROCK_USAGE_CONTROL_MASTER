-- =====================================================
-- Database Creation Script
-- Creates the bedrock_usage database
-- =====================================================

-- Create database (if not created during RDS setup)
CREATE DATABASE IF NOT EXISTS bedrock_usage;

-- Use the database
USE bedrock_usage;

-- Show confirmation
SELECT 'Database bedrock_usage created successfully!' as status;
