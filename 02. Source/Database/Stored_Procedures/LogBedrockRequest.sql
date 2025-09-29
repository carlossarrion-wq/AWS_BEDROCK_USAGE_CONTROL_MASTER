-- =====================================================
-- Stored Procedure: LogBedrockRequest
-- Description: Log a new request
-- =====================================================

DELIMITER //

CREATE PROCEDURE LogBedrockRequest(
    IN p_user_id VARCHAR(255),
    IN p_team VARCHAR(100),
    IN p_model_id VARCHAR(255),
    IN p_model_name VARCHAR(255),
    IN p_request_type VARCHAR(50),
    IN p_input_tokens INT,
    IN p_output_tokens INT,
    IN p_region VARCHAR(50),
    IN p_source_ip VARCHAR(45),
    IN p_user_agent TEXT,
    IN p_session_id VARCHAR(255),
    IN p_request_id VARCHAR(255),
    IN p_response_time_ms INT,
    IN p_status_code INT,
    IN p_error_message TEXT
)
BEGIN
    DECLARE v_cost DECIMAL(10,6) DEFAULT 0.000000;
    DECLARE v_input_price DECIMAL(10,8) DEFAULT 0.00000000;
    DECLARE v_output_price DECIMAL(10,8) DEFAULT 0.00000000;
    
    -- Get model pricing
    SELECT input_token_price, output_token_price
    INTO v_input_price, v_output_price
    FROM model_pricing
    WHERE model_id = p_model_id AND region = p_region
    ORDER BY effective_date DESC
    LIMIT 1;
    
    -- Calculate cost
    SET v_cost = (p_input_tokens * v_input_price / 1000) + (p_output_tokens * v_output_price / 1000);
    
    -- Insert request record
    INSERT INTO bedrock_requests (
        user_id, team, model_id, model_name, request_type,
        input_tokens, output_tokens, cost_usd, region,
        source_ip, user_agent, session_id, request_id,
        response_time_ms, status_code, error_message
    ) VALUES (
        p_user_id, p_team, p_model_id, p_model_name, p_request_type,
        p_input_tokens, p_output_tokens, v_cost, p_region,
        p_source_ip, p_user_agent, p_session_id, p_request_id,
        p_response_time_ms, p_status_code, p_error_message
    );
END //

DELIMITER ;
