-- =====================================================
-- View: v_last_10_days_usage
-- Description: Last 10 days detailed usage
-- =====================================================

CREATE VIEW v_last_10_days_usage AS
SELECT 
    u.user_id,
    u.team,
    u.person_tag,
    dates.date_only,
    COALESCE(r.request_count, 0) as request_count,
    COALESCE(r.total_cost, 0) as total_cost,
    COALESCE(r.unique_models, 0) as unique_models,
    DATEDIFF(CURDATE(), dates.date_only) as days_ago
FROM users u
CROSS JOIN (
    SELECT CURDATE() - INTERVAL n DAY as date_only
    FROM (
        SELECT 0 as n UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4
        UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9
    ) numbers
) dates
LEFT JOIN (
    SELECT 
        user_id,
        date_only,
        COUNT(*) as request_count,
        SUM(cost_usd) as total_cost,
        COUNT(DISTINCT model_id) as unique_models
    FROM bedrock_requests
    GROUP BY user_id, date_only
) r ON u.user_id = r.user_id AND r.date_only = dates.date_only
WHERE dates.date_only >= CURDATE() - INTERVAL 9 DAY;
