-- =====================================================
-- Stored Procedure: CheckUserLimits
-- Description: Check if user should be blocked (called on each request)
-- Extracted from production database: bedrock-usage-mysql.czuimyk2qu10.eu-west-1.rds.amazonaws.com
-- Database: bedrock_usage
-- =====================================================

DELIMITER //

CREATE DEFINER=`admin`@`%` PROCEDURE `CheckUserLimits`(
    IN p_user_id VARCHAR(255)
)
BEGIN
    DECLARE v_daily_request_limit INT DEFAULT 350;
    DECLARE v_monthly_request_limit INT DEFAULT 5000;
    DECLARE v_critical_threshold INT DEFAULT 85;
    DECLARE v_is_blocked BOOLEAN DEFAULT FALSE;
    DECLARE v_blocked_until TIMESTAMP;
    DECLARE v_admin_protection VARCHAR(255);
    DECLARE v_daily_requests_used INT DEFAULT 0;
    DECLARE v_monthly_requests_used INT DEFAULT 0;
    DECLARE v_daily_percent DECIMAL(5,2) DEFAULT 0;
    DECLARE v_monthly_percent DECIMAL(5,2) DEFAULT 0;
    DECLARE v_should_block BOOLEAN DEFAULT FALSE;
    DECLARE v_block_reason VARCHAR(500) DEFAULT NULL;

    -- Get user limits and current status from user_limits table
    SELECT daily_request_limit, monthly_request_limit
    INTO v_daily_request_limit, v_monthly_request_limit
    FROM user_limits
    WHERE user_id = p_user_id;

    -- If user doesn't exist in user_limits, use defaults
    IF v_daily_request_limit IS NULL THEN
        SET v_daily_request_limit = 350;
        SET v_monthly_request_limit = 5000;
    END IF;

    -- Get current daily usage (requests today)
    SELECT COUNT(*)
    INTO v_daily_requests_used
    FROM bedrock_requests
    WHERE user_id = p_user_id
    AND DATE(request_timestamp) = CURDATE();

    -- Get current monthly usage (requests this month)
    SELECT COUNT(*)
    INTO v_monthly_requests_used
    FROM bedrock_requests
    WHERE user_id = p_user_id
    AND DATE(request_timestamp) >= DATE_FORMAT(NOW(), '%Y-%m-01');

    -- Calculate usage percentages
    SET v_daily_percent = (v_daily_requests_used / v_daily_request_limit) * 100;
    SET v_monthly_percent = (v_monthly_requests_used / v_monthly_request_limit) * 100;

    -- Check if user should be blocked based on usage
    IF v_daily_percent >= v_critical_threshold OR v_monthly_percent >= v_critical_threshold THEN
        SET v_should_block = TRUE;
        SET v_block_reason = CONCAT('Usage limit exceeded: Daily: ',
            ROUND(v_daily_percent, 1), '% (', v_daily_requests_used, '/', v_daily_request_limit, '), Monthly: ',
            ROUND(v_monthly_percent, 1), '% (', v_monthly_requests_used, '/', v_monthly_request_limit, ')');
    ELSE
        SET v_should_block = FALSE;
        SET v_block_reason = NULL;
    END IF;

    -- Return results as a SELECT statement (for Lambda function compatibility)
    SELECT
        v_should_block as should_block,
        v_block_reason as block_reason,
        v_daily_requests_used as daily_requests_used,
        v_monthly_requests_used as monthly_requests_used,
        v_daily_percent as daily_percent,
        v_monthly_percent as monthly_percent,
        v_daily_request_limit as daily_limit,
        v_monthly_request_limit as monthly_limit;

END //

DELIMITER ;
