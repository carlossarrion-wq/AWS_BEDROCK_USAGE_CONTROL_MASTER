-- =====================================================
-- Table: model_pricing
-- Description: Model pricing table for cost calculations
-- =====================================================

CREATE TABLE model_pricing (
    model_id VARCHAR(255) PRIMARY KEY,
    model_name VARCHAR(255) NOT NULL,
    input_token_price DECIMAL(10,8) DEFAULT 0.00000000,  -- Price per 1K input tokens
    output_token_price DECIMAL(10,8) DEFAULT 0.00000000, -- Price per 1K output tokens
    region VARCHAR(50) DEFAULT 'us-east-1',
    effective_date DATE DEFAULT (CURDATE()),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_model_region (model_id, region),
    INDEX idx_effective_date (effective_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default model pricing (update with actual AWS Bedrock pricing)
INSERT INTO model_pricing (model_id, model_name, input_token_price, output_token_price) VALUES
('anthropic.claude-3-opus-20240229-v1:0', 'Claude 3 Opus', 0.015000, 0.075000),
('anthropic.claude-3-sonnet-20240229-v1:0', 'Claude 3 Sonnet', 0.003000, 0.015000),
('anthropic.claude-3-haiku-20240307-v1:0', 'Claude 3 Haiku', 0.000250, 0.001250),
('anthropic.claude-3-5-sonnet-20240620-v1:0', 'Claude 3.5 Sonnet', 0.003000, 0.015000),
('amazon.titan-text-express-v1', 'Amazon Titan Text Express', 0.000800, 0.001600),
('amazon.titan-text-lite-v1', 'Amazon Titan Text Lite', 0.000300, 0.000400);
