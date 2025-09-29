-- =====================================================
-- Additional Indexes for Performance Optimization
-- Description: Create additional indexes for performance optimization
-- =====================================================

-- Create indexes for performance optimization
CREATE INDEX idx_requests_user_recent ON bedrock_requests(user_id, request_timestamp DESC);
CREATE INDEX idx_requests_team_recent ON bedrock_requests(team, request_timestamp DESC);
CREATE INDEX idx_requests_model_recent ON bedrock_requests(model_id, request_timestamp DESC);
CREATE INDEX idx_requests_cost_recent ON bedrock_requests(cost_usd DESC, request_timestamp DESC);
