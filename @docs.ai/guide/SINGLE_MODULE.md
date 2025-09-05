# 📄 Single Module Documentation Guide

## 🎯 Quick Summary
Complete guide for documenting a single module, class, or library in one file. Perfect for individual components, API services, or standalone utilities.

## 📋 Table of Contents
1. [When to Use Single File](#when-to-use-single-file)
2. [File Structure Template](#file-structure-template)
3. [Step-by-Step Process](#step-by-step-process)
4. [Real Examples](#real-examples)
5. [Quality Checklist](#quality-checklist)

## 🔑 Key Concepts at a Glance
- **One file**: Everything about the module in single .md file
- **800 lines max**: Keep focused and digestible
- **Self-contained**: No external references needed
- **Copy-paste ready**: All examples work immediately
- **AI-optimized**: Clear structure for LLM understanding

## 🚀 Quick Start (30 minutes)

### When to Use Single File
✅ **Perfect for**:
- Individual Python classes or modules
- Single JavaScript/TypeScript libraries
- REST API endpoints
- Utility functions
- React components
- Database models

❌ **Not suitable for**:
- Multiple related modules
- Complex applications
- Cross-module workflows
- Enterprise systems

---

## 📋 File Structure Template

```markdown
# 📦 Module: [Module Name] %%PRIORITY:HIGH%%

## 🎯 Quick Summary
- [What this module does in 1-2 sentences]
- [Key capabilities and main use cases]

## 📋 Table of Contents
1. [Purpose](#purpose)
2. [Quick Start](#quick-start)
3. [API Reference](#api-reference)
4. [Examples](#examples)
5. [Integration](#integration)
6. [Common Mistakes](#common-mistakes)
7. [Troubleshooting](#troubleshooting)

## 🔑 Key Concepts at a Glance
- **Main Class**: [Primary class name and purpose]
- **Key Functions**: [List 3-5 most important functions]
- **Dependencies**: [Required packages/modules]
- **Return Types**: [What the module produces]

## 🚀 Quick Start
[30-second copy-paste example]

## 📊 API Reference
[Complete function signatures with examples]

## 💡 Usage Examples
[Real-world scenarios with working code]

## 🔗 Integration
[How to use with other modules]

## ❌ Common Mistakes
[Top 3-5 errors and solutions]

## 🐛 Troubleshooting
[Known issues and fixes]

## 🏷️ Metadata
**Tags**: [relevant, keywords, here]
**Added in**: v1.0
**Dependencies**: [list, of, deps]
**Used by**: [modules, that, use, this]
```

---

## 🛠 Step-by-Step Process

### Step 1: Gather Information (5 minutes)
```python
# Answer these questions:
# 1. What is the main purpose of this module?
# 2. What are the 3-5 most important functions/methods?
# 3. What does it depend on?
# 4. What are common use cases?
# 5. What mistakes do people make?

# Example for CarParser module:
main_purpose = "Parse car listings from encar.com with rate limiting"
key_functions = ["parse_car_page", "parse_search_results", "set_delay", "get_statistics"]
dependencies = ["aiohttp", "BeautifulSoup4", "pydantic"]
use_cases = ["Daily import", "Manual search", "Price monitoring"]
common_mistakes = ["No rate limiting", "Missing error handling", "Invalid filters"]
```

### Step 2: Create Working Examples (10 minutes)
```python
# Create examples that actually work
# Use your real domain data, not abstract examples

# ✅ GOOD - Real domain example
car_data = await parser.parse_car_page("https://encar.com/car/123456")
print(f"{car_data.brand} {car_data.model} - {car_data.price:,}₩")

# ❌ BAD - Abstract example
data = await parser.parse("https://example.com/item/123")
print(f"{data.field1} {data.field2}")
```

### Step 3: Document Common Mistakes (5 minutes)
```python
# Think about what goes wrong in practice

common_mistakes = [
    {
        "mistake": "Not setting delays between requests",
        "problem": "Gets IP banned by encar.com",
        "solution": "parser.set_delay(2000)  # 2 second delay",
        "detection": "HTTPError 429 Too Many Requests"
    },
    {
        "mistake": "Parsing without checking page load",
        "problem": "Gets partial or empty data",
        "solution": "await parser.wait_for_content()",
        "detection": "Missing required fields in results"
    }
]
```

### Step 4: Write Integration Notes (5 minutes)
```python
# How does this work with other parts of the system?

integration_patterns = [
    "DatabaseModule: Save results with CarModel.objects.create()",
    "ValidationModule: Validate with CarDataValidator.validate()",
    "QueueModule: Process batches with enqueue_parsing_job()",
    "CacheModule: Cache results with Redis for 1 hour"
]
```

### Step 5: Add Metadata & Polish (5 minutes)
```python
# Final touches for AI optimization

metadata = {
    "tags": ["parsing", "async", "cars", "web-scraping", "encar"],
    "priority": "HIGH",
    "complexity": "MEDIUM",
    "performance": "IO_BOUND",
    "dependencies": ["aiohttp>=3.8", "beautifulsoup4>=4.11", "pydantic>=2.0"]
}
```

---

## 📋 Real Example: CarParser Module

```markdown
# 📦 Module: CarParser %%PRIORITY:HIGH%%

## 🎯 Quick Summary
- Asynchronous parser for encar.com car listings with built-in rate limiting and error handling
- Supports search filtering, pagination, and data validation using Pydantic models

## 📋 Table of Contents
1. [Purpose](#purpose)
2. [Quick Start](#quick-start)
3. [API Reference](#api-reference)
4. [Examples](#examples)
5. [Integration](#integration)
6. [Common Mistakes](#common-mistakes)
7. [Troubleshooting](#troubleshooting)

## 🔑 Key Concepts at a Glance
- **Main Class**: `CarParser` - Async parser with rate limiting
- **Key Functions**: `parse_car_page()`, `parse_search_results()`, `set_delay()`
- **Dependencies**: aiohttp, BeautifulSoup4, pydantic
- **Return Types**: `CarData` and `List[CarData]` Pydantic models

## 🚀 Quick Start

```python
from car_parser import CarParser
from car_parser.models import CarFilters

# Initialize parser with rate limiting
parser = CarParser(delay_ms=2000)

# Parse single car
car = await parser.parse_car_page("https://encar.com/car/123456")
print(f"{car.brand} {car.model} - {car.price:,}₩")

# Search with filters
filters = CarFilters(brand="Toyota", min_price=20000, max_price=40000)
cars = await parser.parse_search_results(filters, max_pages=3)
print(f"Found {len(cars)} Toyota cars")
```

## 📊 API Reference

### CarParser(delay_ms: int = 1000)
Initialize parser with rate limiting.

**Parameters**:
- `delay_ms` (int): Delay between requests in milliseconds

### async parse_car_page(url: str) -> CarData
Parse single car listing page.

**Parameters**:
- `url` (str): Full URL to car listing page

**Returns**: `CarData` object with validated car information

**Raises**:
- `ParsingError`: When page structure is invalid
- `RateLimitError`: When requests are too frequent

```python
car_data = await parser.parse_car_page("https://encar.com/car/123456")
# CarData(id=123456, brand="Hyundai", model="Sonata", year=2023, price=28000000)
```

### async parse_search_results(filters: CarFilters, max_pages: int = 5) -> List[CarData]
Parse search results with filtering and pagination.

**Parameters**:
- `filters` (CarFilters): Search criteria (brand, price range, year, etc.)
- `max_pages` (int): Maximum number of pages to parse

**Returns**: List of `CarData` objects

```python
filters = CarFilters(brand="BMW", year_from=2020, max_price=50000000)
cars = await parser.parse_search_results(filters, max_pages=3)
```

## 💡 Usage Examples

### Daily Import Workflow
```python
from car_parser import CarParser
from car_parser.models import CarFilters
from database import save_cars

async def daily_import():
    parser = CarParser(delay_ms=3000)  # Slower for bulk operations

    # Import popular brands
    brands = ["Hyundai", "Kia", "Genesis", "Samsung"]
    all_cars = []

    for brand in brands:
        filters = CarFilters(brand=brand, year_from=2020)
        cars = await parser.parse_search_results(filters, max_pages=10)
        all_cars.extend(cars)

        print(f"Imported {len(cars)} {brand} cars")
        await asyncio.sleep(5)  # Additional delay between brands

    # Save to database
    await save_cars(all_cars)
    print(f"Total imported: {len(all_cars)} cars")
```

### Price Monitoring
```python
async def monitor_specific_cars(car_urls: List[str]):
    parser = CarParser(delay_ms=5000)  # Very slow for monitoring
    price_changes = []

    for url in car_urls:
        try:
            current_data = await parser.parse_car_page(url)
            # Compare with stored price
            if price_changed(current_data):
                price_changes.append(current_data)
        except ParsingError as e:
            logger.warning(f"Failed to parse {url}: {e}")

    return price_changes
```

## 🔗 Integration

### With Database Module
```python
from database.models import CarModel
from car_parser import CarParser

async def save_parsed_cars():
    cars = await parser.parse_search_results(filters)

    for car_data in cars:
        await CarModel.objects.create(
            encar_id=car_data.id,
            brand=car_data.brand,
            model=car_data.model,
            price=car_data.price,
            imported_at=datetime.utcnow()
        )
```

### With Queue System
```python
from celery_app import enqueue_parsing_job

# Queue individual car parsing
for car_id in car_ids:
    enqueue_parsing_job.delay(f"https://encar.com/car/{car_id}")

# Queue search parsing
enqueue_parsing_job.delay("search", filters.dict(), max_pages=5)
```

## ❌ Common Mistakes

### Mistake 1: No Rate Limiting
**Problem**: Gets IP banned by encar.com within minutes
```python
# ❌ WRONG - Too fast, will get banned
parser = CarParser(delay_ms=100)  # Too fast!
```
**Solution**: Use appropriate delays
```python
# ✅ CORRECT - Safe rate limiting
parser = CarParser(delay_ms=2000)  # 2 second delay minimum
```

### Mistake 2: Not Handling Parsing Errors
**Problem**: Crashes on page structure changes
```python
# ❌ WRONG - No error handling
car = await parser.parse_car_page(url)  # Crashes if page changes
```
**Solution**: Always handle parsing errors
```python
# ✅ CORRECT - Proper error handling
try:
    car = await parser.parse_car_page(url)
except ParsingError as e:
    logger.error(f"Failed to parse {url}: {e}")
    continue
```

### Mistake 3: Invalid Search Filters
**Problem**: No results due to impossible filter combinations
```python
# ❌ WRONG - Impossible filter combination
filters = CarFilters(
    brand="Ferrari",       # Expensive brand
    max_price=10000000    # But low price limit
)
```
**Solution**: Use realistic filter combinations
```python
# ✅ CORRECT - Realistic filters
filters = CarFilters(
    brand="Hyundai",      # Popular brand
    year_from=2018,       # Recent years
    max_price=40000000    # Reasonable price limit
)
```

## 🐛 Troubleshooting

### HTTP 429 - Too Many Requests
**Symptoms**: Getting rate limited by encar.com
**Cause**: Requests too frequent or IP flagged
**Solution**:
```python
# Increase delay and add random variation
parser = CarParser(delay_ms=5000)  # 5 second base delay
await parser.add_random_delay()    # Add 1-3 second random delay
```

### Empty Results
**Symptoms**: `parse_search_results()` returns empty list
**Cause**: Page structure changed or filters too restrictive
**Solution**:
```python
# 1. Check if site structure changed
await parser.debug_page_structure(url)

# 2. Try broader filters
filters = CarFilters(brand="All", year_from=2015)

# 3. Check specific page manually
car = await parser.parse_car_page("https://encar.com/car/123456")
```

### Parsing Errors
**Symptoms**: `ParsingError` exceptions
**Cause**: Website HTML structure changed
**Solution**: Update parsing selectors in parser configuration

## 🏷️ Metadata

**Tags**: `parsing, async, cars, web-scraping, encar, rate-limiting`
**Added in**: v2.0
**Dependencies**:
- `aiohttp>=3.8.0`
- `beautifulsoup4>=4.11.0`
- `pydantic>=2.0.0`
- `lxml>=4.9.0`

**Used by**:
- `@api/car-sync` endpoint
- `@jobs/daily-import` task
- `@admin/manual-import` interface
- `@monitoring/price-tracker` service

%%AI_HINT: This parser includes built-in rate limiting and should be used for all encar.com data extraction%%
```

---

## ✅ Quality Checklist

### Before Publishing
- [ ] **Quick Summary** explains purpose in <30 seconds
- [ ] **Table of Contents** helps find information in <10 seconds
- [ ] **API Reference** has complete function signatures
- [ ] **Examples** use real domain data (not abstract examples)
- [ ] **Common Mistakes** covers actual problems users face
- [ ] **Integration** shows how to use with other modules
- [ ] **File size** < 800 lines for single module docs

### 5-Minute User Test
- [ ] New developer can understand what module does
- [ ] They can copy-paste working example immediately
- [ ] They know what dependencies to install
- [ ] They understand common pitfalls to avoid
- [ ] They can find specific function documentation quickly

### AI Optimization Check
- [ ] Clear section headers for navigation
- [ ] Type-safe examples with Pydantic models
- [ ] No raw dict/Any usage in examples
- [ ] Consistent markdown formatting
- [ ] Metadata tags for searchability

**Time Investment**: 30-60 minutes for comprehensive single module documentation
**Result**: Self-contained, AI-friendly documentation that enables immediate usage
