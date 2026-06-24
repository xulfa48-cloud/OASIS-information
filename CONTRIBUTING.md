# Contributing to ResearchOS

## Code of Conduct

Be respectful, inclusive, and professional.

## Development Setup

1. **Clone & Navigate**
```bash
git clone https://github.com/researchos/researchos.git
cd researchos

```
2.Environment
cp .env.example .env
# Edit .env with your settings

3.Local Services
docker-compose up -d
make migrate
make dev
____
Workflow
Branch Naming

feature/short-description
bugfix/issue-number
refactor/area
docs/topic

____
Commit Messages
type(scope): description

[optional body]
[optional footer]

Examples:
feat(auth): add OAuth2 support
fix(discovery): resolve ranking bug in search
docs(api): update endpoint documentation

Pull Request Process

1.Create feature branch
2.Write tests
3.Ensure all tests pass: make test
4.Lint code: make lint
5.Submit PR with description
6.Address review feedback
7.Squash & merge when approved

Testing:
make test-service SERVICE=auth-service

Integration Tests:
make test-integration

End-to-End Tests:
make test-e2e


Code Standards
Go: Follow Uber Go style guide
TypeScript: ESLint config included
Python: Black formatter, mypy typing
Run make format before committing.

Documentation
Update docs/ for:

API changes
Architecture changes
New services
Configuration updates
Performance Considerations
Keep search latency <500ms
Maintain 99.5% uptime
Cache aggressively
Use async/workers for heavy tasks


Need Help?
Issues: GitHub Issues
Discussions: GitHub Discussions
Slack: #researchos-dev



### .env.example
```bash
# ==== DATABASE ====
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/researchos
REDIS_URL=redis://localhost:6379
QDRANT_URL=http://localhost:6333

# ==== SERVICES ====
AUTH_SERVICE_URL=http://localhost:3001
DISCOVERY_SERVICE_URL=http://localhost:3002
PAPER_SERVICE_URL=http://localhost:3003
KNOWLEDGE_GRAPH_URL=http://localhost:8001
NOVELTY_ENGINE_URL=http://localhost:8002
GAP_ENGINE_URL=http://localhost:8003
AI_COPILOT_URL=http://localhost:8004

# ==== API GATEWAY ====
API_GATEWAY_PORT=8000
API_GATEWAY_HOST=0.0.0.0

# ==== FRONTEND ====
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENVIRONMENT=development

# ==== EXTERNAL SERVICES ====
OPENAI_API_KEY=sk-...
ARXIV_API_URL=https://arxiv.org/api
PUBMED_API_URL=https://pubmed.ncbi.nlm.nih.gov/api
CROSSREF_API_URL=https://api.crossref.org

# ==== AUTH ====
JWT_SECRET=your-secret-key-change-in-production
JWT_EXPIRY=7d
OAUTH_GOOGLE_CLIENT_ID=...
OAUTH_GOOGLE_CLIENT_SECRET=...
OAUTH_GITHUB_CLIENT_ID=...
OAUTH_GITHUB_CLIENT_SECRET=...

# ==== STORAGE ====
S3_BUCKET=researchos-papers
S3_REGION=us-east-1
S3_ACCESS_KEY_ID=...
S3_SECRET_ACCESS_KEY=...

# ==== LOGGING & MONITORING ====
LOG_LEVEL=debug
DATADOG_API_KEY=...
SENTRY_DSN=...

# ==== ENVIRONMENT ====
ENVIRONMENT=development
# Options: development, staging, production





















