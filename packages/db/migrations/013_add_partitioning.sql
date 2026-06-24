-- Migration: 013_add_partitioning.sql
-- Description: Add table partitioning for high-volume tables
-- Created: 2024-01-01

-- Partition auth_audit_logs by month
ALTER TABLE auth_audit_logs SET LOGGED;

-- Create partitioned table for auth logs
CREATE TABLE auth_audit_logs_partitioned (
  id BIGSERIAL,
  user_id UUID,
  event_type VARCHAR(50) NOT NULL,
  ip_address INET,
  user_agent VARCHAR(500),
  status VARCHAR(20) NOT NULL,
  failure_reason VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (DATE_TRUNC('month', created_at));

-- Create monthly partitions for the current year
CREATE TABLE auth_audit_logs_2024_01 PARTITION OF auth_audit_logs_partitioned
  FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE auth_audit_logs_2024_02 PARTITION OF auth_audit_logs_partitioned
  FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

CREATE TABLE auth_audit_logs_2024_03 PARTITION OF auth_audit_logs_partitioned
  FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

CREATE TABLE auth_audit_logs_2024_04 PARTITION OF auth_audit_logs_partitioned
  FOR VALUES FROM ('2024-04-01') TO ('2024-05-01');

CREATE TABLE auth_audit_logs_2024_05 PARTITION OF auth_audit_logs_partitioned
  FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');

CREATE TABLE auth_audit_logs_2024_06 PARTITION OF auth_audit_logs_partitioned
  FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');

CREATE TABLE auth_audit_logs_2024_07 PARTITION OF auth_audit_logs_partitioned
  FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');

CREATE TABLE auth_audit_logs_2024_08 PARTITION OF auth_audit_logs_partitioned
  FOR VALUES FROM ('2024-08-01') TO ('2024-09-01');

CREATE TABLE auth_audit_logs_2024_09 PARTITION OF auth_audit_logs_partitioned
  FOR VALUES FROM ('2024-09-01') TO ('2024-10-01');

CREATE TABLE auth_audit_logs_2024_10 PARTITION OF auth_audit_logs_partitioned
  FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');

CREATE TABLE auth_audit_logs_2024_11 PARTITION OF auth_audit_logs_partitioned
  FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');

CREATE TABLE auth_audit_logs_2024_12 PARTITION OF auth_audit_logs_partitioned
  FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');

-- Partition search_queries by month
CREATE TABLE search_queries_partitioned (
  id BIGSERIAL,
  user_id UUID,
  organization_id UUID,
  query_text VARCHAR(500) NOT NULL,
  search_type VARCHAR(50) NOT NULL,
  result_count INTEGER,
  clicked_result_count INTEGER,
  saved_from_results BOOLEAN DEFAULT false,
  execution_time_ms INTEGER,
  created_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (DATE_TRUNC('month', created_at));

-- Create monthly partitions for search queries
CREATE TABLE search_queries_2024_01 PARTITION OF search_queries_partitioned
  FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE search_queries_2024_02 PARTITION OF search_queries_partitioned
  FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Continue for other months...
CREATE TABLE search_queries_2024_03 PARTITION OF search_queries_partitioned
  FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

CREATE TABLE search_queries_2024_04 PARTITION OF search_queries_partitioned
  FOR VALUES FROM ('2024-04-01') TO ('2024-05-01');

CREATE TABLE search_queries_2024_05 PARTITION OF search_queries_partitioned
  FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');

CREATE TABLE search_queries_2024_06 PARTITION OF search_queries_partitioned
  FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');

CREATE TABLE search_queries_2024_07 PARTITION OF search_queries_partitioned
  FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');

CREATE TABLE search_queries_2024_08 PARTITION OF search_queries_partitioned
  FOR VALUES FROM ('2024-08-01') TO ('2024-09-01');

CREATE TABLE search_queries_2024_09 PARTITION OF search_queries_partitioned
  FOR VALUES FROM ('2024-09-01') TO ('2024-10-01');

CREATE TABLE search_queries_2024_10 PARTITION OF search_queries_partitioned
  FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');

CREATE TABLE search_queries_2024_11 PARTITION OF search_queries_partitioned
  FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');

CREATE TABLE search_queries_2024_12 PARTITION OF search_queries_partitioned
  FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');

-- Partition entity_mentions by year (high volume)
CREATE TABLE entity_mentions_partitioned (
  id BIGSERIAL,
  entity_id UUID NOT NULL,
  paper_id UUID NOT NULL,
  mention_count INTEGER DEFAULT 1,
  first_mention_position INTEGER,
  context_text VARCHAR(500),
  created_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (YEAR(created_at));

CREATE TABLE entity_mentions_2024 PARTITION OF entity_mentions_partitioned
  FOR VALUES FROM (2024) TO (2025);

CREATE TABLE entity_mentions_2025 PARTITION OF entity_mentions_partitioned
  FOR VALUES FROM (2025) TO (2026);
