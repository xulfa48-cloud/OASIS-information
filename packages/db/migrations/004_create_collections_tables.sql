-- Migration: 004_create_collections_tables.sql
-- Description: Collections, saving, and search history tables
-- Created: 2024-01-01

-- Create collections table
CREATE TABLE collections (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
  created_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  collection_type VARCHAR(50) NOT NULL CHECK (collection_type IN ('personal', 'shared_team', 'shared_organization')),
  is_public BOOLEAN DEFAULT false,
  paper_count INTEGER DEFAULT 0,
  tags VARCHAR(100)[],
  color_code VARCHAR(20),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create collection papers table
CREATE TABLE collection_papers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
  paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  added_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  user_notes TEXT,
  rating INTEGER CHECK (rating >= 1 AND rating <= 5),
  date_added TIMESTAMP DEFAULT NOW(),
  date_read TIMESTAMP,
  is_favorite BOOLEAN DEFAULT false,
  UNIQUE(collection_id, paper_id)
);

-- Create collection shares table
CREATE TABLE collection_shares (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
  shared_with_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  shared_with_team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
  permission_level VARCHAR(50) NOT NULL CHECK (permission_level IN ('view', 'comment', 'edit')),
  shared_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT NOW(),
  CHECK (shared_with_user_id IS NOT NULL OR shared_with_team_id IS NOT NULL)
);

-- Create saved searches table
CREATE TABLE saved_searches (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  query VARCHAR(500) NOT NULL,
  search_type VARCHAR(50) NOT NULL CHECK (search_type IN ('keyword', 'semantic', 'hybrid')),
  filters JSONB,
  sort_by VARCHAR(50),
  name VARCHAR(255),
  description TEXT,
  last_executed TIMESTAMP,
  execution_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create saved search results table
CREATE TABLE saved_search_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  saved_search_id UUID NOT NULL REFERENCES saved_searches(id) ON DELETE CASCADE,
  paper_id UUID NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  rank INTEGER,
  score FLOAT,
  snapshot_timestamp TIMESTAMP DEFAULT NOW()
);

-- Create indexes for collections
CREATE INDEX idx_collections_user ON collections(created_by_user_id);
CREATE INDEX idx_collections_organization ON collections(organization_id);
CREATE INDEX idx_collections_type ON collections(collection_type);
CREATE INDEX idx_collections_public ON collections(is_public) WHERE is_public = true;

-- Create indexes for collection papers
CREATE INDEX idx_collection_papers_collection ON collection_papers(collection_id);
CREATE INDEX idx_collection_papers_paper ON collection_papers(paper_id);
CREATE INDEX idx_collection_papers_user ON collection_papers(added_by_user_id);
CREATE INDEX idx_collection_papers_favorite ON collection_papers(collection_id) WHERE is_favorite = true;

-- Create indexes for collection shares
CREATE INDEX idx_collection_shares_collection ON collection_shares(collection_id);
CREATE INDEX idx_collection_shares_user ON collection_shares(shared_with_user_id);
CREATE INDEX idx_collection_shares_team ON collection_shares(shared_with_team_id);

-- Create indexes for saved searches
CREATE INDEX idx_saved_searches_user ON saved_searches(user_id);
CREATE INDEX idx_saved_searches_type ON saved_searches(search_type);
