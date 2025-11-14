# Testing Guide

A comprehensive test suite has been set up for the food tracker application.

## Quick Start

1. **Install testing dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Run all tests:**

   ```bash
   pytest
   ```

3. **Run tests with coverage:**
   ```bash
   pytest --cov=food_tracker --cov-report=html
   ```

## What Was Added

### Test Files Created

- `tests/__init__.py` - Test package initialization
- `tests/conftest.py` - Shared fixtures and test configuration
- `tests/test_models.py` - Tests for domain models (FoodItem, FoodEntry, DailyLog)
- `tests/test_storage.py` - Tests for persistence layer (FoodLogRepository)
- `tests/test_ai.py` - Tests for AI recognition engine
- `tests/test_tracker.py` - Tests for FoodTracker business logic
- `tests/test_api.py` - Tests for FastAPI REST API endpoints
- `tests/README.md` - Detailed testing documentation

### Configuration Files

- `pytest.ini` - Pytest configuration with coverage settings
- Updated `requirements.txt` - Added pytest, pytest-asyncio, pytest-cov, and httpx

## Test Coverage

The test suite covers:

### Models (`test_models.py`)

- ✅ FoodItem creation and matching
- ✅ FoodEntry calories and macros calculation
- ✅ DailyLog aggregation and totals
- ✅ Entry grouping by day

### Storage (`test_storage.py`)

- ✅ Save and load entries
- ✅ Handle missing files
- ✅ Preserve all data fields
- ✅ Legacy format compatibility
- ✅ File overwriting behavior

### AI Recognition (`test_ai.py`)

- ✅ Embedding model encoding
- ✅ Food recognition with various queries
- ✅ Exact and partial matches
- ✅ Alias matching
- ✅ Custom food registration
- ✅ Bulk scanning

### Tracker (`test_tracker.py`)

- ✅ Tracker initialization
- ✅ Food scanning
- ✅ Food logging and persistence
- ✅ Daily summaries
- ✅ Total calories and macros
- ✅ Entry filtering by date

### API (`test_api.py`)

- ✅ Food search endpoint
- ✅ Food library endpoint
- ✅ Food registration endpoint
- ✅ Entry creation and listing
- ✅ Summary endpoint
- ✅ Request validation
- ✅ Response serialization

## Running Specific Tests

```bash
# Run a specific test file
pytest tests/test_models.py

# Run a specific test class
pytest tests/test_models.py::TestFoodItem

# Run a specific test method
pytest tests/test_models.py::TestFoodItem::test_food_item_creation

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=food_tracker --cov-report=term-missing
```

## Test Fixtures

Common fixtures available (defined in `conftest.py`):

- `temp_storage_path` - Temporary file path for storage tests
- `sample_food_item` - Sample FoodItem instance
- `sample_food_entry` - Sample FoodEntry instance
- `repository` - FoodLogRepository with temporary storage
- `recognition_engine` - FoodRecognitionEngine instance
- `tracker` - FoodTracker with test dependencies
- `temp_foods_file` - Temporary foods.json file

## Coverage Report

After running tests with coverage, view the HTML report:

```bash
pytest --cov=food_tracker --cov-report=html
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

## Continuous Integration

To add CI/CD, you can use this in `.github/workflows/tests.yml`:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.9"
      - run: pip install -r requirements.txt
      - run: pytest --cov=food_tracker --cov-report=xml
```

## Next Steps

1. Install dependencies: `pip install -r requirements.txt`
2. Run tests: `pytest`
3. Review coverage: `pytest --cov=food_tracker --cov-report=html`
4. Add more tests as you add features
5. Set up CI/CD for automated testing

## Notes

- All tests use temporary files/directories to avoid affecting production data
- Tests are isolated and can run in any order
- API tests use FastAPI's TestClient for fast, isolated testing
- Storage tests verify data persistence and loading
