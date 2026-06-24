-- Migration: 011_create_system_tables.sql
-- Description: System settings, feature flags, and configuration
-- Created: 2024-01-01

-- Create feature flags table
CREATE TABLE feature_flags (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  flag_name VARCHAR(100) NOT NULL UNIQUE,
  flag_description TEXT,
  enabled BOOLEAN DEFAULT false,
  rollout_percentage INTEGER DEFAULT 0 CHECK (rollout_percentage >= 0 AND rollout_percentage <= 100),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create rate limit rules table
CREATE TABLE rate_limit_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
  requests_per_minute INTEGER,
  requests_per_day INTEGER,
  requests_per_month INTEGER,
  tier VARCHAR(50) NOT NULL CHECK (tier IN ('free', 'professional', 'enterprise')),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create system notifications table
CREATE TABLE system_notifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR(255) NOT NULL,
  message TEXT NOT NULL,
  notification_type VARCHAR(50) NOT NULL CHECK (notification_type IN ('maintenance', 'feature', 'alert')),
  severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'critical')),
  start_date TIMESTAMP NOT NULL,
  end_date TIMESTAMP,
  target_audience VARCHAR(50) NOT NULL CHECK (target_audience IN ('all_users', 'premium_only', 'beta_testers')),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create notification deliveries table
CREATE TABLE notification_deliveries (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  notification_type VARCHAR(50) NOT NULL,
  notification_id UUID,
  status VARCHAR(50) NOT NULL CHECK (status IN ('pending', 'sent', 'failed', 'bounced')),
  sent_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create API rate limit tracking table
CREATE TABLE api_rate_limits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  api_key_id UUID REFERENCES api_keys(id) ON DELETE CASCADE,
  requests_today INTEGER DEFAULT 0,
  requests_this_minute INTEGER DEFAULT 0,
  last_reset TIMESTAMP DEFAULT NOW(),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for feature flags
CREATE INDEX idx_feature_flags_name ON feature_flags(flag_name);
CREATE INDEX idx_feature_flags_enabled ON feature_flags(enabled);

-- Create indexes for rate limit rules
CREATE INDEX idx_rate_limit_user ON rate_limit_rules(user_id);
CREATE INDEX idx_rate_limit_org ON rate_limit_rules(organization_id);
CREATE INDEX idx_rate_limit_tier ON rate_limit_rules(tier);

-- Create indexes for system notifications
CREATE INDEX idx_system_notifications_active ON system_notifications(start_date, end_date);
CREATE INDEX idx_system_notifications_severity ON system_notifications(severity);

-- Create indexes for notification deliveries
CREATE INDEX idx_notification_deliveries_user ON notification_deliveries(user_id);
CREATE INDEX idx_notification_deliveries_status ON notification_deliveries(status);
CREATE INDEX idx_notification_deliveries_date ON notification_deliveries(created_at DESC);

-- Create indexes for rate limits
CREATE INDEX idx_api_rate_limits_user ON api_rate_limits(user_id);
CREATE INDEX idx_api_rate_limits_key ON api_rate_limits(api_key_id);
