# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

**This is a LexIQ Nova-customized fork of LiteLLM.** It serves as the **universal gateway for all LexIQ Nova elements** - embeddings, chat models, VL models, and other specialized Nova capabilities.

### Key Customizations
- **Nova Task Routing**: Custom hook in `litellm/proxy/hooks/nova_task_routing.py` for intelligent task-based model selection
- **Nova Model Configurations**: Task-specific adapters for embeddings (retrieval, text-matching, code) in `proxy_server_config.yaml`
- **Tag-based Routing**: Enables automatic model selection based on task type using the router's tag filtering system
- **Wildcard Routing**: Support for all Nova model variants via `remodlai/*` pattern

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
- **Database**: `db/` - Prisma ORM with PostgreSQL/SQLite support
- **Management endpoints**: `management_endpoints/` - Admin APIs for keys, teams, models
- **Pass-through endpoints**: `pass_through_endpoints/` - Provider-specific API forwarding
- **Guardrails**: `guardrails/` - Safety and content filtering hooks
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
- YAML config files for proxy server (see `proxy/example_config_yaml/`)
- Environment variables for API keys and settings
- Database schema managed via Prisma (`proxy/schema.prisma`)

### Hooks System
- Proxy hooks for custom logic in `litellm/proxy/hooks/`
- Register hooks in YAML config via `litellm_settings.callbacks`
- Available built-in hooks: `max_budget_limiter`, `parallel_request_limiter`, `cache_control_check`
- Hook factory: `get_proxy_hook(hook_name)` in `litellm/proxy/hooks/__init__.py`
- Enterprise hooks auto-loaded from `enterprise/enterprise_hooks.py`

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

### Database Migrations
- Prisma handles schema migrations
- Migration files auto-generated with `prisma migrate dev`
- Always test migrations against both PostgreSQL and SQLite

### Enterprise Features
- Enterprise-specific code in `enterprise/` directory
- Optional features enabled via environment variables
- Separate licensing and authentication for enterprise features

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