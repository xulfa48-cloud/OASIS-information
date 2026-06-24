# Data Models

## Overview

This document describes the core data models used throughout the OASIS system.

## Entity Relationship Diagram

```
┌─────────────┐         ┌──────────────┐
│    User     │◄───────►│   Profile    │
└─────────────┘         └──────────────┘
      │                       
      │ owns                  
      ▼                       
┌─────────────┐         ┌──────────────┐
│  Resource   │◄───────►│     Tags     │
└─────────────┘         └──────────────┘
      │                       
      │ contains              
      ▼                       
┌─────────────┐         
│  Version    │         
└─────────────┘         

┌─────────────┐         ┌──────────────┐
│ Collection  │◄───────►│  Resource    │
└─────────────┘         └──────────────┘

┌─────────────┐         ┌──────────────┐
│ Permission  │◄───────►│   Role       │
└─────────────┘         └──────────────┘
```

## Core Models

### User

Represents a system user account.

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  username VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
  last_login TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  INDEX(email),
  INDEX(username),
  INDEX(status)
);
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `email` | String | Email address (unique) |
| `username` | String | Display username |
| `password_hash` | String | Bcrypt hashed password |
| `first_name` | String | User's first name |
| `last_name` | String | User's last name |
| `status` | Enum | Account status |
| `last_login` | Timestamp | Last login time |
| `created_at` | Timestamp | Account creation time |
| `updated_at` | Timestamp | Last update time |

---

### Profile

Extended user profile information.

```sql
CREATE TABLE profiles (
  id UUID PRIMARY KEY,
  user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  avatar_url VARCHAR(500),
  bio TEXT,
  timezone VARCHAR(50),
  locale VARCHAR(10),
  theme ENUM('light', 'dark', 'auto') DEFAULT 'auto',
  notifications_enabled BOOLEAN DEFAULT TRUE,
  two_factor_enabled BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  FOREIGN KEY(user_id) REFERENCES users(id)
);
```

---

### Resource

Core resource object in the system.

```sql
CREATE TABLE resources (
  id UUID PRIMARY KEY,
  owner_id UUID NOT NULL REFERENCES users(id),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  type VARCHAR(50) NOT NULL,
  content JSONB,
  status ENUM('draft', 'published', 'archived') DEFAULT 'draft',
  visibility ENUM('private', 'shared', 'public') DEFAULT 'private',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  deleted_at TIMESTAMP,
  
  INDEX(owner_id),
  INDEX(type),
  INDEX(status),
  INDEX(visibility),
  INDEX(created_at),
  FULLTEXT INDEX(name, description)
);
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique resource ID |
| `owner_id` | UUID | Resource owner |
| `name` | String | Resource name |
| `description` | Text | Resource description |
| `type` | String | Resource type (document, project, etc) |
| `content` | JSONB | Resource content (flexible structure) |
| `status` | Enum | Draft, published, or archived |
| `visibility` | Enum | Private, shared, or public |
| `created_at` | Timestamp | Creation time |
| `updated_at` | Timestamp | Last update time |
| `deleted_at` | Timestamp | Soft delete time |

---

### Version

Version history for resources.

```sql
CREATE TABLE versions (
  id UUID PRIMARY KEY,
  resource_id UUID NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
  version_number INT NOT NULL,
  created_by UUID NOT NULL REFERENCES users(id),
  content JSONB NOT NULL,
  change_summary VARCHAR(500),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(resource_id, version_number),
  INDEX(resource_id),
  INDEX(created_at)
);
```

---

### Collection

Grouping of resources.

```sql
CREATE TABLE collections (
  id UUID PRIMARY KEY,
  owner_id UUID NOT NULL REFERENCES users(id),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  icon VARCHAR(50),
  color VARCHAR(7),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  INDEX(owner_id)
);
```

---

### Tag

Tags for resource categorization.

```sql
CREATE TABLE tags (
  id UUID PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL,
  color VARCHAR(7),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  INDEX(name)
);

CREATE TABLE resource_tags (
  resource_id UUID NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
  tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  
  PRIMARY KEY(resource_id, tag_id)
);
```

---

### Permission

Fine-grained access control.

```sql
CREATE TABLE permissions (
  id UUID PRIMARY KEY,
  resource_id UUID NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role ENUM('viewer', 'commenter', 'editor', 'admin') NOT NULL,
  granted_by UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP,
  
  UNIQUE(resource_id, user_id),
  INDEX(user_id),
  INDEX(role)
);
```

**Roles:**

| Role | Permissions |
|------|-------------|
| `viewer` | Read-only access |
| `commenter` | Read + comment |
| `editor` | Read + write |
| `admin` | Full control + share |

---

### Comment

Discussion comments on resources.

```sql
CREATE TABLE comments (
  id UUID PRIMARY KEY,
  resource_id UUID NOT NULL REFERENCES resources(id) ON DELETE CASCADE,
  author_id UUID NOT NULL REFERENCES users(id),
  content TEXT NOT NULL,
  parent_comment_id UUID REFERENCES comments(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  INDEX(resource_id),
  INDEX(author_id),
  INDEX(parent_comment_id)
);
```

---

### Activity Log

Audit trail for all actions.

```sql
CREATE TABLE activity_logs (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  action VARCHAR(100) NOT NULL,
  resource_id UUID REFERENCES resources(id),
  resource_type VARCHAR(50),
  changes JSONB,
  ip_address VARCHAR(45),
  user_agent VARCHAR(500),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  INDEX(user_id),
  INDEX(resource_id),
  INDEX(action),
  INDEX(created_at)
);
```

---

## Data Type Guidelines

### UUID
- Use for all primary and foreign keys
- Generated using UUIDv4
- Immutable after creation

### Timestamps
- Use UTC timezone
- Include both `created_at` and `updated_at`
- Support soft deletes with `deleted_at`

### Enums
- Use for fixed set of values
- More efficient than strings
- Defined at schema level

### JSON/JSONB
- Use JSONB (binary JSON) for PostgreSQL
- Enables flexible schema for resource content
- Indexable for performance

### Large Text
- Use TEXT for content > 1000 chars
- Use VARCHAR(255) for names/titles
- Use LONGTEXT for very large content

---

## Relationships

### One-to-Many

User → Resources (one user owns many resources)

```sql
ALTER TABLE resources ADD COLUMN owner_id UUID REFERENCES users(id);
```

### Many-to-Many

Resources ↔ Tags (many resources can have many tags)

```sql
CREATE TABLE resource_tags (
  resource_id UUID REFERENCES resources(id),
  tag_id UUID REFERENCES tags(id),
  PRIMARY KEY(resource_id, tag_id)
);
```

### Polymorphic

Single comment model for multiple resource types

```sql
CREATE TABLE comments (
  id UUID PRIMARY KEY,
  resource_type VARCHAR(50),
  resource_id UUID,
  content TEXT
);
```

---

## Indexing Strategy

### Primary Keys
- UUID primary key on all tables

### Foreign Keys
- Index all foreign key columns

### Frequent Queries
- Index on commonly filtered columns
- Example: `user_id`, `status`, `created_at`

### Full-Text Search
- FULLTEXT INDEX on searchable fields
- Example: resource name, description

### Partitioning (for large tables)
```sql
CREATE TABLE activity_logs_2026_06 PARTITION OF activity_logs
  FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
```

---

## Data Constraints

### Uniqueness
- User email and username must be unique
- Resource name unique per owner
- Tag name globally unique

### Not Null
- user_id (ownership requirement)
- name (identification requirement)
- created_at (audit trail requirement)

### Check Constraints
```sql
ALTER TABLE users ADD CONSTRAINT check_email FORMAT email;
ALTER TABLE resources ADD CONSTRAINT check_positive_views CHECK(view_count >= 0);
```

---

## Migration Strategy

### Adding Fields

```sql
-- Add new column with default
ALTER TABLE resources ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Update existing rows
UPDATE resources SET updated_at = created_at WHERE updated_at IS NULL;

-- Make NOT NULL if required
ALTER TABLE resources ALTER COLUMN updated_at SET NOT NULL;
```

### Removing Fields

```sql
-- Check dependencies first
SELECT * FROM information_schema.referential_constraints 
WHERE table_name = 'resources';

-- Drop column
ALTER TABLE resources DROP COLUMN deprecated_field;
```

---
*Last Updated: 2026-06-24*
