-- =====================================================
-- Table: bedrock_requests
-- Description: Individual request records table - stores every single request
-- =====================================================

CREATE TABLE bedrock_requests (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    team VARCHAR(100) NOT NULL,
    request_timestamp TIMESTAMP(3) DEFAULT CURRENT_TIMESTAMP(3),
    date_only DATE GENERATED ALWAYS AS (DATE(request_timestamp)) STORED,
    hour_only INT GENERATED ALWAYS AS (HOUR(request_timestamp)) STORED,
    model_id VARCHAR(255) NOT NULL,
    model_name VARCHAR(255),
    request_type ENUM('invoke', 'invoke-stream', 'converse', 'converse-stream') DEFAULT 'invoke',
    input_tokens INT DEFAULT 0,
    output_tokens INT DEFAULT 0,
    total_tokens INT GENERATED ALWAYS AS (input_tokens + output_tokens) STORED,
    cost_usd DECIMAL(10,6) DEFAULT 0.000000,
    region VARCHAR(50) DEFAULT 'us-east-1',
    source_ip VARCHAR(45),
    user_agent TEXT,
    session_id VARCHAR(255),
    request_id VARCHAR(255),
    response_time_ms INT DEFAULT 0,
    status_code INT DEFAULT 200,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    INDEX idx_user_timestamp (user_id, request_timestamp),
    INDEX idx_user_date (user_id, date_only),
    INDEX idx_team_timestamp (team, request_timestamp),
    INDEX idx_team_date (team, date_only),
    INDEX idx_model_timestamp (model_id, request_timestamp),
    INDEX idx_timestamp (request_timestamp),
    INDEX idx_date_hour (date_only, hour_only),
    INDEX idx_user_date_hour (user_id, date_only, hour_only),
    INDEX idx_team_date_hour (team, date_only, hour_only),
    INDEX idx_model_date (model_id, date_only),
    INDEX idx_cost (cost_usd),
    INDEX idx_tokens (total_tokens),
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Partition the requests table by date for better performance
ALTER TABLE bedrock_requests 
PARTITION BY RANGE (TO_DAYS(date_only)) (
    PARTITION p_2025_01 VALUES LESS THAN (TO_DAYS('2025-02-01')),
    PARTITION p_2025_02 VALUES LESS THAN (TO_DAYS('2025-03-01')),
    PARTITION p_2025_03 VALUES LESS THAN (TO_DAYS('2025-04-01')),
    PARTITION p_2025_04 VALUES LESS THAN (TO_DAYS('2025-05-01')),
    PARTITION p_2025_05 VALUES LESS THAN (TO_DAYS('2025-06-01')),
    PARTITION p_2025_06 VALUES LESS THAN (TO_DAYS('2025-07-01')),
    PARTITION p_2025_07 VALUES LESS THAN (TO_DAYS('2025-08-01')),
    PARTITION p_2025_08 VALUES LESS THAN (TO_DAYS('2025-09-01')),
    PARTITION p_2025_09 VALUES LESS THAN (TO_DAYS('2025-10-01')),
    PARTITION p_2025_10 VALUES LESS THAN (TO_DAYS('2025-11-01')),
    PARTITION p_2025_11 VALUES LESS THAN (TO_DAYS('2025-12-01')),
    PARTITION p_2025_12 VALUES LESS THAN (TO_DAYS('2026-01-01')),
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
