-- =====================================================
-- View: v_user_realtime_usage
-- Description: Real-time user usage aggregation by hour
-- Extracted from production database: bedrock-usage-mysql.czuimyk2qu10.eu-west-1.rds.amazonaws.com
-- Database: bedrock_usage
-- Date: 2025-09-23 21:30:29
-- =====================================================

CREATE ALGORITHM=UNDEFINED DEFINER=`admin`@`%` SQL SECURITY DEFINER VIEW `v_user_realtime_usage` AS 
select 
    `bedrock_requests`.`user_id` AS `user_id`,
    `bedrock_requests`.`team` AS `team`,
    cast(`bedrock_requests`.`request_timestamp` as date) AS `usage_date`,
    hour(`bedrock_requests`.`request_timestamp`) AS `usage_hour`,
    count(0) AS `request_count`,
    sum(`bedrock_requests`.`input_tokens`) AS `total_input_tokens`,
    sum(`bedrock_requests`.`output_tokens`) AS `total_output_tokens`,
    sum(`bedrock_requests`.`total_tokens`) AS `total_tokens`,
    sum(`bedrock_requests`.`cost_usd`) AS `total_cost`,
    avg(`bedrock_requests`.`processing_time_ms`) AS `avg_processing_time` 
from `bedrock_requests` 
group by 
    `bedrock_requests`.`user_id`,
    `bedrock_requests`.`team`,
    cast(`bedrock_requests`.`request_timestamp` as date),
    hour(`bedrock_requests`.`request_timestamp`);
