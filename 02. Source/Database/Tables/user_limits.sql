-- =====================================================
-- Table: user_limits
-- Description: Stores user information and quotas
-- Extracted from production database: bedrock-usage-mysql.czuimyk2qu10.eu-west-1.rds.amazonaws.com
-- Database: bedrock_usage
-- =====================================================

CREATE TABLE `user_limits` (
  `user_id` varchar(255) NOT NULL,
  `team` varchar(100) NOT NULL,
  `person` varchar(100) DEFAULT 'Unknown',
  `daily_request_limit` int NOT NULL DEFAULT '350',
  `monthly_request_limit` int NOT NULL DEFAULT '5000',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `administrative_safe` char(1) NOT NULL DEFAULT 'N' COMMENT 'Y=Usuario protegido del bloqueo automático, N=Sin protección',
  PRIMARY KEY (`user_id`),
  KEY `idx_team` (`team`),
  KEY `idx_user_team` (`user_id`,`team`),
  KEY `idx_user_limits_admin_safe` (`administrative_safe`),
  CONSTRAINT `chk_administrative_safe` CHECK ((`administrative_safe` in (_utf8mb4'Y',_utf8mb4'N')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Insert default system user
INSERT IGNORE INTO user_limits (user_id, team, person) VALUES 
('system', 'admin', 'System User');
