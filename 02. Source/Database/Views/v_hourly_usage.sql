-- =====================================================
-- View: v_hourly_usage
-- Description: Hourly usage analysis
-- =====================================================

CREATE VIEW v_hourly_usage AS
SELECT 
    user_id,
    team,
    date_only,
    hour_only,
    COUNT(*) as request_count,
    COUNT(DISTINCT model_id) as unique_models,
    SUM(input_tokens) as total_input_tokens,
    SUM(output_tokens) as total_output_tokens,
    SUM(total_tokens) as total_tokens,
    SUM(cost_usd) as total_cost,
    AVG(response_time_ms) as avg_response_time,
    MIN(request_timestamp) as first_request,
    MAX(request_timestamp) as last_request
FROM bedrock_requests
GROUP BY user_id, team, date_only, hour_only;
