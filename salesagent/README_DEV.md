# orcs2-salesagent Dev Quick Start

Quick setup guide for developers working on the orcs2-salesagent project.

## 1. Prerequisites

- Python 3.8+ (`python3 --version`)
- pip (`pip --version`)
- make (`make --version`)
- git (`git --version`)

## 2. Setup

### Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Environment Configuration
```bash
# Copy example environment file
cp .env.example .env  # if .env.example exists

# Edit .env with your configuration
# Minimum required keys:
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=sqlite:///./orcs2.db
```

## 3. Start the Server

### Quick Start (Recommended)
```bash
make dev
```

### Manual Start
```bash
# Check environment first
python scripts/check_env.py

# Start Flask development server
python -m flask --app src.admin.app:app run --host=0.0.0.0 --port=8000 --debug --reload
```

### Server URLs
- **Health Check**: http://localhost:8000/health
- **Buyer UI**: http://localhost:8000/buyer
- **Admin UI**: http://localhost:8000/admin
- **Campaign Builder**: http://localhost:8000/buyer/campaign/new

## 4. Run Tests

### Quick Tests
```bash
make test
```

### With Coverage
```bash
make cov
```

### Individual Test Files
```bash
pytest tests/unit/phase7/test_payload_mapper_shape.py -v
pytest tests/e2e/test_smokes.py -v
```

## 5. Common Gotchas in Cursor

### Working Directory Issues

**Problem**: Terminal opens in wrong directory
```bash
# Check current directory
pwd
ls

# If not in repo root, navigate there
cd /path/to/orcs2-salesagent
```

**Solution**: Always verify you're in the repository root
```bash
git rev-parse --show-toplevel
# Should print: /path/to/orcs2-salesagent
```

### Terminal Launch Errors

**Problem**: "posix_spawnp failed" or terminal won't start
- Close all integrated terminals
- Reopen Cursor
- Ensure shell is set to bash/zsh in Cursor settings
- Check that working directory exists

### Python Path Issues

**Problem**: `uvicorn: command not found`
```bash
# ❌ Don't use this
uvicorn app.main:app --reload

# ✅ Use this instead
python -m uvicorn app.main:app --reload
```

### Port Conflicts

**Problem**: "Address already in use"
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
PORT=8001 make dev
```

### Virtual Environment Issues

**Problem**: Packages not found after installation
```bash
# Verify virtual environment is active
echo $VIRTUAL_ENV

# Reactivate if needed
source venv/bin/activate

# Reinstall packages
pip install -r requirements.txt
```

### Environment Variables

**Problem**: Environment variables not loaded
```bash
# Check if .env file exists
ls -la .env

# Load manually if needed
export $(grep -v '^#' .env | xargs)

# Or use the check script
python scripts/check_env.py
```

## 6. Development Workflow

### Daily Development
```bash
# 1. Activate environment
source venv/bin/activate

# 2. Check environment
make check-env

# 3. Start server
make dev

# 4. In another terminal, run tests
make test
```

### Code Quality
```bash
# Format code
make format

# Check linting
make lint

# Run all checks
make check
```

### Database Operations
```bash
# Run migrations
python scripts/migrate_add_buyer_campaigns.py

# Reset database (if needed)
rm orcs2.db
python scripts/migrate_add_buyer_campaigns.py
```

## 7. Troubleshooting

### Server Won't Start
1. Check working directory: `pwd`
2. Verify virtual environment: `echo $VIRTUAL_ENV`
3. Check dependencies: `python -c "import flask, sqlalchemy"`
4. Check port availability: `lsof -i :8000`
5. Run environment check: `make check-env`

### Tests Failing
1. Check Python version: `python --version`
2. Verify test dependencies: `pip list | grep pytest`
3. Run individual test: `pytest tests/unit/phase7/test_payload_mapper_shape.py -v`
4. Check for import errors: `python -c "from services.ad_payload_mapper import AdPayloadMapper"`

### Import Errors
1. Verify you're in the right directory
2. Check virtual environment is active
3. Reinstall packages: `pip install -r requirements.txt`
4. Check Python path: `python -c "import sys; print(sys.path)"`

## 8. File Structure

```
orcs2-salesagent/
├── api/                    # API routers
├── scripts/               # Development scripts
├── src/                   # Main application code
│   ├── admin/            # Admin UI
│   ├── core/             # Core functionality
│   ├── repositories/     # Data access layer
│   └── services/         # Business logic
├── templates/            # Jinja2 templates
├── tests/               # Test files
├── Makefile             # Development commands
├── requirements.txt     # Python dependencies
└── README_DEV.md       # This file
```

## 9. Quick Reference

| Command | Description |
|---------|-------------|
| `make dev` | Start development server |
| `make test` | Run tests quickly |
| `make cov` | Run tests with coverage |
| `make lint` | Check code quality |
| `make format` | Format code |
| `make check-env` | Verify environment |
| `make clean` | Clean temporary files |

## 10. Getting Help

- Check this README first
- Run `make check-env` for environment issues
- Check test output for specific errors
- Verify you're in the correct directory
- Ensure virtual environment is active

**Remember**: Always run `make check-env` when starting development to catch common issues early!
