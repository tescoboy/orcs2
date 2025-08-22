# Development Guide

## Local Development Setup

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Git
- uv (Python package manager): `pip install uv`

### Initial Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/adcontextprotocol/salesagent.git
   cd salesagent
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start services:**
   ```bash
   docker-compose up -d
   ```

5. **Initialize database:**
   ```bash
   uv run python migrate.py
   uv run python init_database.py
   ```

### Running the Services

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Access points:
- MCP Server: http://localhost:8080/mcp/
- Admin UI: http://localhost:8001
- PostgreSQL: localhost:5432

## Conductor Development Environment

Conductor is a Mac app for running multiple development workspaces in parallel. Each workspace gets its own git worktree and isolated Docker environment.

### Conductor Prerequisites

Set these environment variables in your shell (add to `~/.bashrc` or `~/.zshrc`):

```bash
# Required for Admin UI access
export SUPER_ADMIN_EMAILS='your-email@example.com'
export SUPER_ADMIN_DOMAINS='example.com'  # Optional

# Required for AI features
export GEMINI_API_KEY='your-gemini-api-key'

# Required for Google OAuth
export GOOGLE_CLIENT_ID='your-client-id.apps.googleusercontent.com'
export GOOGLE_CLIENT_SECRET='your-client-secret'
```

### Conductor Port Management

The system uses a predefined pool of ports to avoid OAuth redirect URI updates:

1. **Configure Google OAuth redirect URLs:**
   ```bash
   python manage_conductor_ports.py oauth-urls
   ```

   Add these URLs to your Google OAuth app:
   - http://localhost:8002/auth/google/callback
   - http://localhost:8003/auth/google/callback
   - ... through port 8011

2. **Reserve a port for your workspace:**
   ```bash
   python manage_conductor_ports.py reserve --workspace my-feature
   ```

3. **Release port when done:**
   ```bash
   python manage_conductor_ports.py release --workspace my-feature
   ```

### Setting Up a Conductor Workspace

Run the automated setup script from within your Conductor workspace:

```bash
./setup_conductor_workspace.sh
```

This script:
- Detects the Conductor workspace automatically
- Assigns unique ports based on workspace name
- Creates `.env` with proper configuration
- Creates `docker-compose.override.yml` for hot-reloading
- Installs Git hooks for the workspace

### Conductor Workspace Structure

```
.conductor/
├── workspace-name/           # Git worktree
│   ├── .env                 # Auto-generated config
│   ├── docker-compose.override.yml  # Dev overrides
│   └── (project files)
├── another-workspace/
│   └── ...
```

### Managing Multiple Workspaces

```bash
# List all workspaces and their ports
python manage_conductor_ports.py status

# Clean up a workspace
./cleanup_conductor_workspace.sh workspace-name

# View workspace logs
cd .conductor/workspace-name
docker-compose logs -f
```

## Creating Ad Server Adapters

### Base Adapter Structure

```python
from src.adapters.base import AdServerAdapter
from src.core.schemas import *

class MyPlatformAdapter(AdServerAdapter):
    adapter_name = "myplatform"

    def __init__(self, config, principal, dry_run=False, creative_engine=None):
        super().__init__(config, principal, dry_run, creative_engine)
        self.advertiser_id = self.principal.get_adapter_id("myplatform")

    def create_media_buy(self, request, packages, start_time, end_time):
        # Implementation

    def get_avails(self, request):
        # Implementation

    def activate_media_buy(self, media_buy_id):
        # Implementation
```

### Required Methods

1. **get_avails** - Check inventory availability
2. **create_media_buy** - Create campaigns/orders
3. **activate_media_buy** - Activate pending campaigns
4. **pause_media_buy** - Pause active campaigns
5. **get_media_buy_status** - Get campaign status
6. **get_media_buy_performance** - Get performance metrics

### Adapter Configuration UI

Adapters can provide custom configuration interfaces:

```python
def get_config_ui_endpoint(self) -> Optional[str]:
    return f"/adapters/{self.adapter_name}/config"

def register_ui_routes(self, app, db_session_factory):
    @app.route(self.get_config_ui_endpoint() + "/<tenant_id>/<product_id>")
    def config_ui(tenant_id, product_id):
        # Render configuration UI

def validate_product_config(self, config: dict) -> tuple[bool, Optional[str]]:
    # Validate adapter-specific configuration
```

## Targeting System

### Targeting Capabilities

The system supports two-tier targeting:

1. **Overlay Dimensions** - Available to principals
   - Geography, demographics, interests, devices
   - AEE signals, contextual targeting

2. **Managed-Only Dimensions** - Internal use only
   - Platform-specific optimizations
   - Reserved inventory segments

### Platform Mapping

Each adapter translates AdCP targeting to platform-specific format:

```python
def _translate_targeting(self, overlay):
    platform_targeting = {}

    if "geo_country_any_of" in overlay:
        platform_targeting["location"] = {
            "countries": overlay["geo_country_any_of"]
        }

    if "signals" in overlay:
        platform_targeting["custom_targeting"] = {
            "keys": self._map_signals(overlay["signals"])
        }

    return platform_targeting
```

## Testing

### Running Tests

```bash
# All tests
uv run pytest

# Specific category
uv run pytest tests/unit/
uv run pytest tests/integration/

# With coverage
uv run pytest --cov=. --cov-report=html

# Inside Docker
docker exec -it adcp-server pytest
```

### Test Categories

- **Unit Tests** - Component isolation tests
- **Integration Tests** - Full workflow tests
- **Adapter Tests** - Platform-specific tests
- **UI Tests** - Admin interface tests

### Simulation Testing

```bash
# Full lifecycle simulation
uv run python run_simulation.py

# Dry-run mode (logs API calls)
uv run python run_simulation.py --dry-run --adapter gam

# Custom scenarios
uv run python simulation_full.py http://localhost:8080 \
  --token "test_token" \
  --principal "test_principal"
```

## Database Development

### Schema Changes

1. Check existing schema first:
```bash
grep -r "Column(" models.py
sqlite3 adcp_local.db ".schema table_name"
```

2. Create migration:
```bash
uv run alembic revision -m "add_new_column"
```

3. Edit migration file:
```python
def upgrade():
    op.add_column('table_name',
        sa.Column('new_column', sa.String(100)))

def downgrade():
    op.drop_column('table_name', 'new_column')
```

4. Test migration:
```bash
# Test on copy
cp adcp_local.db test.db
DATABASE_URL=sqlite:///test.db uv run python migrate.py
```

### Database Best Practices

- Always use SQLAlchemy's `sa.table()` in migrations
- Handle both SQLite and PostgreSQL differences
- Use scoped sessions for thread safety
- Test with both database types

## API Development

### MCP Tools

Tools are exposed via FastMCP:

```python
@app.tool
async def get_products(
    context: Context,
    brief: Optional[str] = None
) -> GetProductsResponse:
    # Get auth from headers
    auth_token = context.http.headers.get("x-adcp-auth")

    # Resolve principal and tenant
    principal, tenant = await resolve_auth(auth_token)

    # Return products
    return GetProductsResponse(products=products)
```

### Adding New Tools

1. Define schema in `schemas.py`
2. Implement tool in `main.py`
3. Add tests in `test_main.py`
4. Update documentation

## UI Development

### Template Development

- Always extend `base.html`
- Use Bootstrap classes (loaded in base)
- Avoid global CSS resets
- Test element visibility

### JavaScript Best Practices

```javascript
// Handle nulls
const value = (data.field || 'default');

// Check elements exist
const element = document.getElementById('id');
if (element) {
    // Safe to use
}

// API calls with error handling
try {
    const response = await fetch('/api/endpoint', {
        credentials: 'same-origin'
    });
    if (!response.ok) throw new Error('Failed');
    const data = await response.json();
} catch (error) {
    console.error('API error:', error);
}
```

## Security Considerations

### Authentication

- MCP uses `x-adcp-auth` header tokens
- Admin UI uses Google OAuth
- Principals have unique tokens per advertiser
- Super admins configured via environment

### Audit Logging

All operations are logged to database:

```python
from audit_logger import AuditLogger

logger = AuditLogger(db_session)
logger.log(
    operation="create_media_buy",
    principal_id=principal.principal_id,
    tenant_id=tenant_id,
    success=True,
    details={"media_buy_id": result.media_buy_id}
)
```

## Development Workflow

### Git Workflow

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes and test:**
   ```bash
   # Run tests
   uv run pytest

   # Check formatting
   black --check .
   ruff check .
   ```

3. **Commit with descriptive message:**
   ```bash
   git add .
   git commit -m "feat: add new targeting dimension"
   ```

4. **Push and create PR:**
   ```bash
   git push origin feature/my-feature
   ```

### Commit Message Format

```
type(scope): description

Detailed explanation if needed

Fixes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Test changes
- `chore`: Maintenance

### Pre-commit Hooks

Install Git hooks for code quality:

```bash
./setup_hooks.sh
```

Hooks run:
- Black (code formatting)
- Ruff (linting)
- Unit tests
- Type checking (mypy)

## Code Style and Standards

### Python Style Guide

- Follow PEP 8
- Use type hints for all functions
- Maximum line length: 100 characters
- Use descriptive variable names
- Document all public methods

### Code Organization

```python
# Imports order
import standard_library
import third_party

from local_app import modules

# Class structure
class MyClass:
    """Class description."""

    def __init__(self):
        """Initialize."""
        pass

    def public_method(self) -> str:
        """Public method description."""
        return self._private_method()

    def _private_method(self) -> str:
        """Private method description."""
        return "result"
```

## Debugging

### Docker Debugging

```bash
# View container logs
docker-compose logs -f adcp-server

# Execute commands in container
docker exec -it adcp-buy-server-adcp-server-1 bash

# Check container health
docker ps

# Rebuild containers
docker-compose build --no-cache
docker-compose up -d
```

### Python Debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use IPython
import IPython; IPython.embed()

# Run with debugger
python -m pdb script.py
```

### MCP Server Debugging

```bash
# Use MCP Inspector
npm install -g @modelcontextprotocol/inspector
npx inspector http://localhost:8080/mcp/

# View server logs
docker-compose logs -f adcp-server

# Test with curl
curl -H "x-adcp-auth: your_token" \
     http://localhost:8080/mcp/tools/get_products
```

### Database Debugging

```bash
# Connect to PostgreSQL
docker exec -it adcp-buy-server-postgres-1 psql -U adcp_user -d adcp

# Common queries
SELECT * FROM tenants;
SELECT * FROM principals WHERE tenant_id = 'tenant_123';
SELECT * FROM media_buys ORDER BY created_at DESC LIMIT 10;

# Check migrations
SELECT * FROM alembic_version;
```

## Common Patterns

### Error Handling

```python
try:
    result = perform_operation()
except ValidationError as e:
    return {"error": str(e)}, 400
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return {"error": "Internal error"}, 500
finally:
    db_session.remove()
```

### Database Sessions

```python
from sqlalchemy.orm import scoped_session

db_session = scoped_session(SessionLocal)
try:
    db_session.remove()  # Start fresh
    # Do work
    db_session.commit()
except Exception:
    db_session.rollback()
    raise
finally:
    db_session.remove()
```
