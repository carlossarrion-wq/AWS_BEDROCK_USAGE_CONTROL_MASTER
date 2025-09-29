-- =====================================================
-- Stored Procedure: ExecuteUserBlocking
-- Description: Execute user blocking with CET timestamps
-- =====================================================

DELIMITER //

CREATE PROCEDURE ExecuteUserBlocking(
    IN p_user_id VARCHAR(255),
    IN p_block_reason VARCHAR(500),
    IN p_performed_by VARCHAR(255),
    IN p_current_requests INT,
    IN p_daily_limit INT
)
BEGIN
    DECLARE v_blocked_until TIMESTAMP;
    DECLARE v_previous_status CHAR(1) DEFAULT 'N';
    DECLARE v_usage_percentage DECIMAL(5,2);
    DECLARE v_current_cet_time TIMESTAMP;
    
    -- Get current CET time by converting from UTC
    SET v_current_cet_time = CONVERT_TZ(NOW(), 'UTC', 'Europe/Madrid');
    
    -- Calculate unblock date (tomorrow at 00:00 CET)
    SET v_blocked_until = CONVERT_TZ(DATE_ADD(DATE(CONVERT_TZ(NOW(), 'UTC', 'Europe/Madrid')), INTERVAL 1 DAY), 'Europe/Madrid', 'UTC');
    
    -- Calculate usage percentage
    SET v_usage_percentage = (p_current_requests / p_daily_limit) * 100;
    
    -- Get previous status if exists
    SELECT is_blocked INTO v_previous_status
    FROM users
    WHERE user_id = p_user_id;
    
    -- Update user blocking status with CET timestamps
    UPDATE users 
    SET is_blocked = TRUE,
        blocked_reason = p_block_reason,
        blocked_until = v_blocked_until,
        updated_at = CONVERT_TZ(NOW(), 'UTC', 'Europe/Madrid')
    WHERE user_id = p_user_id;
    
    -- Log blocking operation in audit trail with CET timestamp
    INSERT INTO blocking_operations (
        user_id, operation, reason, performed_by,
        expires_at, created_at
    ) VALUES (
        p_user_id, 'block', p_block_reason, p_performed_by,
        CONVERT_TZ(v_blocked_until, 'UTC', 'Europe/Madrid'),
        CONVERT_TZ(NOW(), 'UTC', 'Europe/Madrid')
    );
    
END //

DELIMITER ;
