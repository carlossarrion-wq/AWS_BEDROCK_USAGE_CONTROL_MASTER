-- Fix for sap_003 showing as "system" instead of "Carlos Sarrión"
-- This script addresses the root cause and cleans up the data

-- Step 1: Clean up erroneous "system" records from bedrock_requests table
-- These are blocking action records that should never have been inserted
DELETE FROM bedrock_usage.bedrock_requests 
WHERE user_id = 'sap_003' 
  AND team = 'system' 
  AND person = 'system' 
  AND model_id = 'BLOCKING_ACTION';

-- Step 2: Ensure sap_003 has correct person information in user_limits table
INSERT INTO bedrock_usage.user_limits (
    user_id, 
    team, 
    person, 
    daily_request_limit, 
    monthly_request_limit, 
    created_at, 
    updated_at
) VALUES (
    'sap_003', 
    'team_sap_group', 
    'Carlos Sarrión', 
    350, 
    5000, 
    NOW(), 
    NOW()
) ON DUPLICATE KEY UPDATE
    person = 'Carlos Sarrión',
    team = 'team_sap_group',
    updated_at = NOW();

-- Step 3: Update any existing legitimate bedrock_requests records for sap_003 
-- that might have incorrect person information
UPDATE bedrock_usage.bedrock_requests br
JOIN bedrock_usage.user_limits ul ON br.user_id = ul.user_id
SET br.person = ul.person,
    br.team = ul.team
WHERE br.user_id = 'sap_003'
  AND br.model_id != 'BLOCKING_ACTION'  -- Don't update blocking action records (they should be deleted)
  AND (br.person != ul.person OR br.team != ul.team);

-- Step 4: Verify the fix
SELECT 'Current user_limits record for sap_003:' as info;
SELECT user_id, team, person, daily_request_limit, monthly_request_limit 
FROM bedrock_usage.user_limits 
WHERE user_id = 'sap_003';

SELECT 'Sample bedrock_requests records for sap_003 (should show Carlos Sarrión):' as info;
SELECT user_id, team, person, model_id, request_timestamp 
FROM bedrock_usage.bedrock_requests 
WHERE user_id = 'sap_003' 
ORDER BY request_timestamp DESC 
LIMIT 5;

SELECT 'Count of remaining BLOCKING_ACTION records (should be 0):' as info;
SELECT COUNT(*) as blocking_action_count
FROM bedrock_usage.bedrock_requests 
WHERE user_id = 'sap_003' 
  AND model_id = 'BLOCKING_ACTION';
