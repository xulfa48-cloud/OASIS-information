-- Migration: 012_add_foreign_keys.sql
-- Description: Add all foreign key constraints
-- Created: 2024-01-01

-- Add foreign key for users.institution_id (self-referential through organizations)
ALTER TABLE users
ADD CONSTRAINT fk_users_institution
FOREIGN KEY (institution_id) REFERENCES organizations(id) ON DELETE SET NULL;

-- Add foreign key for organizations.created_by_user_id
ALTER TABLE organizations
ADD CONSTRAINT fk_org_created_by
FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL;

-- Add foreign key for paper_content.paper_id (already exists)
-- Verify that all paper_content rows have corresponding papers

-- Add foreign key for paper_citations to handle both directions
-- Check for orphaned citations
DELETE FROM paper_citations 
WHERE citing_paper_id NOT IN (SELECT id FROM papers) 
   OR cited_paper_id NOT IN (SELECT id FROM papers);

-- Verify all collections have proper references
-- Organizations can be null (personal collections)
-- But created_by_user_id must exist
ALTER TABLE collections
ADD CONSTRAINT check_collection_owner
CHECK (created_by_user_id IS NOT NULL);

-- Verify all comments reference either paper or annotation
ALTER TABLE comments
ADD CONSTRAINT check_comment_has_reference
CHECK (paper_id IS NOT NULL OR annotation_id IS NOT NULL);

-- Verify collection shares have a recipient
ALTER TABLE collection_shares
ADD CONSTRAINT check_share_recipient
CHECK (shared_with_user_id IS NOT NULL OR shared_with_team_id IS NOT NULL);

-- Verify data export requests are properly linked
ALTER TABLE data_export_requests
ADD CONSTRAINT check_export_user
CHECK (user_id IS NOT NULL);

-- Verify audit logs have context
ALTER TABLE audit_logs
ADD CONSTRAINT check_audit_context
CHECK (user_id IS NOT NULL OR organization_id IS NOT NULL);

-- Verify RAG retrievals reference correct message type
ALTER TABLE rag_retrievals
ADD CONSTRAINT check_rag_assistant_message
CHECK (
  EXISTS (
    SELECT 1 FROM copilot_messages 
    WHERE id = message_id AND message_type = 'assistant'
  )
);

-- Verify fact checks are in completed sessions
ALTER TABLE fact_checks
ADD CONSTRAINT check_fact_check_session
CHECK (
  EXISTS (
    SELECT 1 FROM copilot_sessions 
    WHERE id = session_id AND ended_at IS NOT NULL
  )
);

-- Add constraint for portfolio entries to have either project or paper
ALTER TABLE portfolio_entries
ADD CONSTRAINT check_portfolio_reference
CHECK (project_id IS NOT NULL OR paper_id IS NOT NULL);

-- Ensure novelty scores are within valid range
ALTER TABLE novelty_scores
ADD CONSTRAINT check_novelty_range
CHECK (novelty_score >= 0 AND novelty_score <= 100);

-- Ensure gap scores are within valid range
ALTER TABLE research_gaps
ADD CONSTRAINT check_gap_scores
CHECK (
  impact_score >= 0 AND impact_score <= 100 AND
  difficulty_score >= 0 AND difficulty_score <= 100 AND
  resource_requirement_score >= 0 AND resource_requirement_score <= 100 AND
  opportunity_score >= 0 AND opportunity_score <= 100
);

-- Ensure confidence scores are probabilities
ALTER TABLE fact_checks
ADD CONSTRAINT check_confidence_range
CHECK (confidence_score >= 0 AND confidence_score <= 1);

-- Ensure rating is valid
ALTER TABLE collection_papers
ADD CONSTRAINT check_rating_range
CHECK (rating IS NULL OR (rating >= 1 AND rating <= 5));

-- Ensure annotation color codes are valid hex
ALTER TABLE annotations
ADD CONSTRAINT check_hex_color
CHECK (color_code ~ '^#[0-9A-Fa-f]{6}$' OR color_code IS NULL);

-- Ensure rollout percentage is valid
ALTER TABLE feature_flags
ADD CONSTRAINT check_rollout_range
CHECK (rollout_percentage >= 0 AND rollout_percentage <= 100);
