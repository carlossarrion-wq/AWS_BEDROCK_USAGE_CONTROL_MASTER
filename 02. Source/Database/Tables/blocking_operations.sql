-- =====================================================
-- Table: blocking_operations
-- Description: Blocking operations log table - audit trail
-- =====================================================

CREATE TABLE blocking_operations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    operation ENUM('block', 'unblock', 'admin_protect', 'admin_unprotect') NOT NULL,
    reason VARCHAR(500),
    performed_by VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_operation (operation),
    INDEX idx_performed_by (performed_by),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
