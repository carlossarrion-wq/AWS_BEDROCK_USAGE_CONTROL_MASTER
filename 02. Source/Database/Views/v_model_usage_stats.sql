-- =====================================================
-- View: v_model_usage_stats
-- Description: Model usage statistics
-- =====================================================

CREATE VIEW v_model_usage_stats AS
SELECT 
    r.model_id,
    r.model_name,
    r.team,
    r.date_only,
    COUNT(*) as request_count,
    COUNT(DISTINCT r.user_id) as unique_users,
    SUM(r.input_tokens) as total_input_tokens,
    SUM(r.output_tokens) as total_output_tokens,
    SUM(r.total_tokens) as total_tokens,
    SUM(r.cost_usd) as total_cost,
    AVG(r.response_time_ms) as avg_response_time
FROM bedrock_requests r
GROUP BY r.model_id, r.model_name, r.team, r.date_only;
