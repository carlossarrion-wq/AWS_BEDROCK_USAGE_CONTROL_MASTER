-- =====================================================
-- View: v_team_usage_dashboard
-- Description: Team usage dashboard
-- =====================================================

CREATE VIEW v_team_usage_dashboard AS
SELECT 
    team,
    date_only,
    COUNT(*) as total_requests,
    COUNT(DISTINCT user_id) as active_users,
    COUNT(DISTINCT model_id) as unique_models,
    SUM(input_tokens) as total_input_tokens,
    SUM(output_tokens) as total_output_tokens,
    SUM(cost_usd) as total_cost,
    AVG(response_time_ms) as avg_response_time,
    MIN(request_timestamp) as first_request,
    MAX(request_timestamp) as last_request
FROM bedrock_requests
GROUP BY team, date_only;
