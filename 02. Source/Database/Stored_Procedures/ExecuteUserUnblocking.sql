-- =====================================================
-- Stored Procedure: ExecuteUserUnblocking
-- Description: Execute user unblocking with CET timestamps
-- =====================================================

DELIMITER //

CREATE PROCEDURE ExecuteUserUnblocking(
    IN p_user_id VARCHAR(255),
    IN p_unblock_reason VARCHAR(500),
    IN p_performed_by VARCHAR(255)
)
BEGIN
    DECLARE v_previous_status CHAR(1) DEFAULT 'Y';
    
    -- Update user blocking status with CET timestamps
    UPDATE users 
    SET is_blocked = FALSE,
        blocked_reason = p_unblock_reason,
        blocked_until = NULL,
        updated_at = CONVERT_TZ(NOW(), 'UTC', 'Europe/Madrid')
    WHERE user_id = p_user_id;
    
    -- Log unblocking operation in audit trail with CET timestamp
    INSERT INTO blocking_operations (
        user_id, operation, reason, performed_by,
        expires_at, created_at
    ) VALUES (
        p_user_id, 'unblock', p_unblock_reason, p_performed_by,
        NULL,
        CONVERT_TZ(NOW(), 'UTC', 'Europe/Madrid')
    );
    
END //

DELIMITER ;
