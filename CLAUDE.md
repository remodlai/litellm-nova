# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

**This is a LexIQ Nova-customized fork of LiteLLM.** It serves as the **universal gateway for all LexIQ Nova elements** - embeddings, chat models, VL models, and other specialized Nova capabilities.

### Key Customizations

#### License Bypass & Enterprise Mode
**CRITICAL**: This fork bypasses the standard LiteLLM license checks to enable all enterprise features:

- **License bypass location**: `litellm/proxy/auth/litellm_license.py`
- **Modified methods**:
  - `is_premium()`: Always returns `True` (lines 96-130)
  - `verify_license_without_api_request()`: Always returns `True` (line 158-159)
- **Effect**: Enables all enterprise features without requiring a license key:
  - Tag-based budget limiting (`litellm/router_strategy/budget_limiter.py`)
  - Google/Hashicorp/CyberArk secret managers (`litellm/secret_managers/`)
  - Custom guardrail modes (`enterprise/litellm_enterprise/`)
  - Callback controls via headers
- **Usage**: `premium_user` variable in `proxy_server.py` is set from `_license_check.is_premium()` (line 540)

#### Nova Task Routing Hook
- **Location**: `litellm/proxy/hooks/nova_task_routing.py`
- **Purpose**: Converts Nova's `task` parameter to LiteLLM's tag-based routing
- **How it works**:
  - Intercepts embedding requests with `task` parameter (e.g., `"retrieval.passage"`)
  - Transforms to tag-based routing: `metadata.tags = ["retrieval.passage"]`
  - Router selects deployment with matching tags
- **Registration**: Add to `litellm_settings.callbacks` in config YAML
- **Example tasks**: `retrieval.query`, `retrieval.passage`, `text-matching`, `code.query`, `code.passage`

#### Nova Model Configurations
- **Config file**: `proxy_server_config.yaml`
- **Model patterns**:
  - `nova-embeddings-v1` with task-specific adapters
  - `remodlai/*` wildcard for all Nova variants
- **Task adapters**:
  - `remodlai/nova-embeddings-v1-retrieval` (tags: retrieval, retrieval.query, retrieval.passage)
  - `remodlai/nova-embeddings-v1-text-matching` (tags: text-matching)
  - `remodlai/nova-embeddings-v1-code` (tags: code, code.query, code.passage)
- **Router settings**: `enable_tag_filtering: True` required for task-based routing

#### Cold Storage & Logging
- **S3 cold storage**: `s3_callback_params` configured for `remodl-cold-storage` bucket
- **MLflow callbacks**: Enabled for success/failure tracking
- **Session logging**: All prompts stored in spend logs and cold storage

### Related Agents
- **Refactor Agent** (this agent): Handles LiteLLM gateway customization and integration
- **Vector Agent**: Works on VL model deployment
- Communication via task assignment based on `@graphiti/entities/task.py`

## Development Commands

### Installation
- `make install-dev` - Install core development dependencies
- `make install-proxy-dev` - Install proxy development dependencies with full feature set
- `make install-test-deps` - Install all test dependencies

### Testing
- `make test` - Run all tests
- `make test-unit` - Run unit tests (tests/test_litellm) with 4 parallel workers
- `make test-integration` - Run integration tests (excludes unit tests)
- `pytest tests/` - Direct pytest execution

### Code Quality
- `make lint` - Run all linting (Ruff, MyPy, Black, circular imports, import safety)
- `make format` - Apply Black code formatting
- `make lint-ruff` - Run Ruff linting only
- `make lint-mypy` - Run MyPy type checking only

### Single Test Files
- `poetry run pytest tests/path/to/test_file.py -v` - Run specific test file
- `poetry run pytest tests/path/to/test_file.py::test_function -v` - Run specific test
- `make test-llm-translation` - Run LLM provider translation tests
- `make test-llm-translation-single FILE=test_filename.py` - Run single provider test file

### Running Scripts
- `poetry run python script.py` - Run Python scripts (use for non-test files)

### GitHub Issue & PR Templates
When contributing to the project, use the appropriate templates:

**Bug Reports** (`.github/ISSUE_TEMPLATE/bug_report.yml`):
- Describe what happened vs. what you expected
- Include relevant log output
- Specify your LiteLLM version

**Feature Requests** (`.github/ISSUE_TEMPLATE/feature_request.yml`):
- Describe the feature clearly
- Explain the motivation and use case

**Pull Requests** (`.github/pull_request_template.md`):
- Add at least 1 test in `tests/litellm/`
- Ensure `make test-unit` passes

## Architecture Overview

LiteLLM is a unified interface for 100+ LLM providers with two main components:

### Core Library (`litellm/`)
- **Main entry point**: `litellm/main.py` - Contains core completion() function
- **Provider implementations**: `litellm/llms/` - Each provider has its own subdirectory
- **Router system**: `litellm/router.py` + `litellm/router_utils/` - Load balancing and fallback logic
- **Type definitions**: `litellm/types/` - Pydantic models and type hints
- **Integrations**: `litellm/integrations/` - Third-party observability, caching, logging
- **Caching**: `litellm/caching/` - Multiple cache backends (Redis, in-memory, S3, etc.)

### Proxy Server (`litellm/proxy/`)
- **Main server**: `proxy_server.py` - FastAPI application
- **Authentication**: `auth/` - API key management, JWT, OAuth2
  - **License check**: `auth/litellm_license.py` - Modified to always return `premium_user = True`
- **Database**: `db/` - Prisma ORM with PostgreSQL/SQLite support
- **Management endpoints**: `management_endpoints/` - Admin APIs for keys, teams, models
- **Pass-through endpoints**: `pass_through_endpoints/` - Provider-specific API forwarding
- **Guardrails**: `guardrails/` - Safety and content filtering hooks
- **Hooks**: `hooks/` - Custom logic injection points
  - **Nova task routing**: `hooks/nova_task_routing.py` - Task-to-tag conversion
- **UI Dashboard**: Served from `_experimental/out/` (Next.js build)

## Key Patterns

### Provider Implementation
- Providers inherit from base classes in `litellm/llms/base.py`
- Each provider has transformation functions for input/output formatting
- Support both sync and async operations
- Handle streaming responses and function calling

### Error Handling
- Provider-specific exceptions mapped to OpenAI-compatible errors
- Fallback logic handled by Router system
- Comprehensive logging through `litellm/_logging.py`

### Configuration
- YAML config files for proxy server (see `proxy_server_config.yaml`)
- Environment variables for API keys and settings
- Database schema managed via Prisma (`proxy/schema.prisma`)

### Hooks System
- Proxy hooks for custom logic in `litellm/proxy/hooks/`
- Register hooks in YAML config via `litellm_settings.callbacks`
- Available built-in hooks: `max_budget_limiter`, `parallel_request_limiter`, `cache_control_check`
- Hook factory: `get_proxy_hook(hook_name)` in `litellm/proxy/hooks/__init__.py`
- **Nova hooks**: `nova_task_router` for task-based routing
- Enterprise hooks auto-loaded from `enterprise/enterprise_hooks.py`

### Nova Task Routing Flow
1. Client sends request: `POST /embeddings {"model": "nova-embeddings-v1", "task": "retrieval.query", ...}`
2. `NovaTaskRoutingHook.async_pre_call_hook()` intercepts request
3. Hook converts `task` to `metadata.tags = ["retrieval.query"]`
4. Router (with `enable_tag_filtering: True`) selects deployment with matching tag
5. Request forwarded to correct Nova adapter (e.g., `remodlai/nova-embeddings-v1-retrieval`)

## Development Notes

### Package Management
- Uses Poetry for dependency management
- Install with `poetry install` or use Makefile targets
- Core dependencies pinned: `openai>=1.99.5`, `pydantic^2.5.0`
- Proxy features require `[proxy]` extra: `pip install 'litellm[proxy]'`
- Development setup requires both `[dev]` and `[proxy-dev]` groups

### Code Style
- Uses Black formatter, Ruff linter, MyPy type checker
- Pydantic v2 for data validation
- Async/await patterns throughout
- Type hints required for all public APIs
- Follows Google Python Style Guide

### Testing Strategy
- Unit tests in `tests/test_litellm/`
- Integration tests for each provider in `tests/llm_translation/`
- Proxy tests in `tests/proxy_unit_tests/`
- Load tests in `tests/load_tests/`
- License tests in `tests/test_litellm/proxy/auth/test_litellm_license.py`

### Database Migrations
- Prisma handles schema migrations
- Migration files auto-generated with `prisma migrate dev`
- Always test migrations against both PostgreSQL and SQLite

### Enterprise Features
- **All enterprise features enabled by default via license bypass**
- Enterprise-specific code in `enterprise/` directory
- Optional features controllable via environment variables
- No license key required due to `is_premium()` always returning `True`

## Running the Proxy Server Locally

### Quick Start
```bash
# Install proxy dependencies
make install-proxy-dev

# Start proxy with config file
litellm --config proxy_server_config.yaml

# Or use the Python CLI directly
python litellm/proxy_cli.py
```

### With Database (PostgreSQL)
```bash
# Setup environment
echo 'LITELLM_MASTER_KEY="sk-1234"' > .env
echo 'LITELLM_SALT_KEY="your-random-hash"' >> .env
source .env

# Start with Docker Compose (includes Postgres + Prometheus)
docker compose up
```

### Frontend Dashboard
```bash
cd ui/litellm-dashboard
npm install
npm run dev
```

## Modifying License/Enterprise Behavior

If you need to modify license checks or enterprise features:

1. **License bypass**: Edit `litellm/proxy/auth/litellm_license.py`
   - `is_premium()`: Controls enterprise feature availability (currently always `True`)
   - `verify_license_without_api_request()`: Local license validation (currently always `True`)

2. **Premium user checks**: Search for `premium_user` in codebase
   - Set in `proxy_server.py` line 540: `premium_user: bool = _license_check.is_premium()`
   - Used throughout proxy for feature gating

3. **Testing**: Run `poetry run pytest tests/test_litellm/proxy/auth/test_litellm_license.py`
