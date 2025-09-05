# 📄📄 Multi-Module Documentation Guide (2-3 Files)

## 🎯 Quick Summary
Guide for documenting related modules, small applications, or feature sets using 2-3 focused files. Perfect for microservices, plugin systems, or cohesive module groups.

## 📋 Table of Contents
1. [When to Use Multi-Module](#when-to-use-multi-module)
2. [File Organization Strategy](#file-organization-strategy)
3. [Step-by-Step Process](#step-by-step-process)
4. [Real Example: Car Import System](#real-example-car-import-system)
5. [Quality Checklist](#quality-checklist)

## 🔑 Key Concepts at a Glance
- **2-3 files**: Each focused on specific functionality area
- **1000 lines max** per file to stay AI-friendly
- **Clear navigation**: index.md + specialized files
- **Cross-references**: Link between files when needed
- **Cohesive system**: Files work together to tell complete story

## 🚀 Quick Start (2-4 hours)

### When to Use Multi-Module
✅ **Perfect for**:
- Feature systems (2-5 related modules)
- Microservices with multiple components
- Plugin architectures
- API services with multiple endpoints
- Import/export systems
- Authentication/authorization systems

❌ **Use single file instead**:
- Individual classes or utilities
- Simple libraries
- Single API endpoints

❌ **Use app documentation instead**:
- Complete applications (5+ major areas)
- Enterprise systems
- Multi-team projects

---

## 📁 File Organization Strategy

### Option 1: Functional Split (Most Common)
```
index.md          # Overview, navigation, quick start
core.md           # Main functionality and business logic
integrations.md   # External connections and data flow
```

### Option 2: Layer Split
```
index.md          # Overview and architecture
data-layer.md     # Models, database, storage
service-layer.md  # Business logic, processing, APIs
```

### Option 3: Domain Split
```
index.md          # System overview
parsing.md        # Data extraction and parsing
storage.md        # Data persistence and retrieval
```

---

## 🛠 Step-by-Step Process

### Step 1: Define File Boundaries (15 minutes)
```python
# Analyze your system and group related functionality

system_analysis = {
    "total_modules": 4,  # CarParser, DataValidator, DatabaseSaver, NotificationService
    "main_workflows": ["Import cars", "Validate data", "Save to DB", "Notify admin"],
    "external_dependencies": ["encar.com", "PostgreSQL", "Redis", "Email service"],
    "internal_connections": {
        "CarParser -> DataValidator": "Raw data validation",
        "DataValidator -> DatabaseSaver": "Clean data storage",
        "DatabaseSaver -> NotificationService": "Import completion"
    }
}

# Group into logical files:
files = {
    "index.md": "Overview, architecture, quick start",
    "parsing-validation.md": "CarParser + DataValidator (core data flow)",
    "storage-notifications.md": "DatabaseSaver + NotificationService (persistence)"
}
```

### Step 2: Create Navigation Structure (10 minutes)
```markdown
# index.md structure
- System overview and purpose
- Architecture diagram/flow
- Quick start example
- Links to detailed files
- Troubleshooting entry points

# Specialized files structure
- File-specific table of contents
- Modules covered in this file
- Cross-references to other files
- Detailed examples and patterns
```

### Step 3: Plan Cross-References (10 minutes)
```python
cross_references = {
    "from_index": [
        "See [parsing-validation.md] for data processing details",
        "See [storage-notifications.md] for persistence layer"
    ],
    "between_files": [
        "parsing-validation.md -> storage-notifications.md (data flow)",
        "storage-notifications.md -> index.md (troubleshooting)"
    ]
}
```

### Step 4: Write Files in Order (90-150 minutes)
1. **index.md** (30-45 min): Overview, navigation, quick start
2. **core functionality file** (45-60 min): Main business logic
3. **supporting functionality file** (30-45 min): Integrations, persistence

### Step 5: Cross-Link and Polish (15 minutes)
- Add navigation links between files
- Verify examples work across files
- Check file sizes (<1000 lines each)
- Validate cross-references

---

## 📋 Real Example: Car Import System

### File Structure Decision
```python
# System: Daily car import from encar.com
modules = [
    "CarParser",           # Parse car data from website
    "DataValidator",       # Validate and clean data
    "DatabaseSaver",       # Save to PostgreSQL
    "NotificationService"  # Send completion emails
]

# Logical grouping:
files = {
    "index.md": "System overview, architecture, quick start",
    "data-processing.md": "CarParser + DataValidator (data pipeline)",
    "persistence.md": "DatabaseSaver + NotificationService (storage & alerts)"
}
```

### index.md Example
```markdown
# 🚗 Car Import System Documentation

## 🎯 Quick Summary
- Automated daily import system for car listings from encar.com
- Validates, processes, and stores car data with email notifications

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Detailed Documentation](#detailed-documentation)
5. [Troubleshooting](#troubleshooting)

## 🔑 Key Components at a Glance
- **CarParser**: Extracts car data from encar.com with rate limiting
- **DataValidator**: Validates and cleans car data using Pydantic
- **DatabaseSaver**: Persists car data to PostgreSQL with deduplication
- **NotificationService**: Sends import status emails to admins

## 🏗️ System Architecture

```
encar.com → CarParser → DataValidator → DatabaseSaver → PostgreSQL
                             ↓               ↓
                      ValidationErrors    Success/Failure
                             ↓               ↓
                     NotificationService ←────┘
                             ↓
                         Admin Email
```

## 🚀 Quick Start

```python
from car_import_system import CarImportPipeline
from car_import_system.models import ImportConfig

# Configure import
config = ImportConfig(
    max_pages=5,
    brands=["Hyundai", "Kia", "Genesis"],
    notification_emails=["admin@company.com"]
)

# Run daily import
pipeline = CarImportPipeline(config)
result = await pipeline.run_daily_import()

print(f"Imported {result.cars_added} cars, {result.errors} errors")
```

## 📚 Detailed Documentation

### 🔄 [Data Processing](./data-processing.md)
**Covers**: CarParser + DataValidator
- Web scraping with rate limiting
- Data validation and cleaning
- Error handling patterns
- Performance optimization

### 💾 [Persistence Layer](./persistence.md)
**Covers**: DatabaseSaver + NotificationService
- Database operations and deduplication
- Email notification system
- Monitoring and alerting
- Backup and recovery

## 🐛 Common Issues

### Import Failures
**Symptoms**: No new cars imported
**Check**:
1. [Data Processing - Rate Limiting](./data-processing.md#rate-limiting)
2. [Persistence - Database Connection](./persistence.md#database-connection)

### Validation Errors
**Symptoms**: High error rate in import logs
**Solution**: See [Data Processing - Validation Rules](./data-processing.md#validation-rules)

### Missing Notifications
**Symptoms**: No email alerts received
**Solution**: See [Persistence - Email Configuration](./persistence.md#email-configuration)

## 🏷️ Metadata
**Tags**: `car-import, parsing, validation, automation, encar`
**Added in**: v2.0
**Dependencies**: aiohttp, pydantic, sqlalchemy, aiosmtplib
```

### data-processing.md Example
```markdown
# 🔄 Data Processing: Parsing & Validation

## 🎯 Quick Summary
Detailed documentation for CarParser and DataValidator modules - the core data processing pipeline that extracts and validates car data from encar.com.

## 📋 Table of Contents
1. [CarParser Module](#carparser-module)
2. [DataValidator Module](#datavalidator-module)
3. [Integration Pattern](#integration-pattern)
4. [Error Handling](#error-handling)
5. [Performance Tuning](#performance-tuning)

## 🔑 Modules in This File
- **CarParser**: Web scraping with async + rate limiting
- **DataValidator**: Pydantic-based validation and cleaning

---

## 🕷️ CarParser Module

### Purpose
Asynchronous web parser for encar.com with built-in rate limiting and robust error handling.

### Core Functions

#### async parse_daily_listings(filters: SearchFilters) -> List[RawCarData]
Main entry point for daily import operations.

```python
from car_import_system import CarParser
from car_import_system.models import SearchFilters

parser = CarParser(delay_ms=3000)  # 3 second delays for bulk import

filters = SearchFilters(
    brands=["Hyundai", "Kia"],
    year_from=2020,
    max_pages=10
)

raw_cars = await parser.parse_daily_listings(filters)
print(f"Extracted {len(raw_cars)} raw car records")
```

#### Rate Limiting Strategy
```python
class RateLimitConfig:
    base_delay_ms: int = 3000      # 3 seconds between requests
    random_delay_ms: int = 1000    # Add 0-1 second random delay
    backoff_multiplier: float = 2.0 # Double delay on rate limit errors
    max_retries: int = 3           # Retry failed requests
```

### Error Handling Patterns
```python
try:
    cars = await parser.parse_daily_listings(filters)
except RateLimitError as e:
    logger.warning(f"Rate limited, waiting {e.retry_after}s")
    await asyncio.sleep(e.retry_after)
except ParsingError as e:
    logger.error(f"Parsing failed: {e.details}")
    # Continue with next batch
except NetworkError as e:
    logger.error(f"Network issue: {e}")
    # Implement exponential backoff
```

---

## ✅ DataValidator Module

### Purpose
Validates and cleans raw car data using Pydantic v2 models with custom business rules.

### Validation Models

```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from decimal import Decimal

class CarData(BaseModel):
    """Validated car data model."""

    encar_id: int = Field(..., gt=0)
    brand: str = Field(..., min_length=1, max_length=50)
    model: str = Field(..., min_length=1, max_length=100)
    year: int = Field(..., ge=1990, le=2025)
    price: Decimal = Field(..., gt=0, le=Decimal('500000000'))  # Max 500M KRW
    mileage: Optional[int] = Field(None, ge=0)

    @validator('brand')
    def normalize_brand(cls, v):
        return v.strip().title()

    @validator('price')
    def validate_price_range(cls, v, values):
        year = values.get('year')
        if year and year < 2000 and v > Decimal('50000000'):
            raise ValueError('Old cars cannot be that expensive')
        return v
```

### Validation Pipeline
```python
from car_import_system import DataValidator
from car_import_system.models import ValidationReport

validator = DataValidator()

# Validate batch of raw car data
raw_cars = await parser.parse_daily_listings(filters)
validation_result = await validator.validate_batch(raw_cars)

print(f"Valid: {len(validation_result.valid_cars)}")
print(f"Invalid: {len(validation_result.invalid_cars)}")
print(f"Error rate: {validation_result.error_rate:.2%}")

# Get detailed error report
for error in validation_result.validation_errors:
    print(f"Car {error.encar_id}: {error.error_message}")
```

---

## 🔗 Integration Pattern

### Complete Data Processing Flow
```python
async def process_daily_import():
    """Complete data processing pipeline."""

    # Step 1: Parse raw data
    parser = CarParser(delay_ms=3000)
    raw_cars = await parser.parse_daily_listings(filters)

    # Step 2: Validate and clean
    validator = DataValidator()
    validation_result = await validator.validate_batch(raw_cars)

    # Step 3: Handle validation results
    if validation_result.error_rate > 0.1:  # >10% error rate
        logger.warning(f"High error rate: {validation_result.error_rate:.2%}")
        # Send alert - see persistence.md for NotificationService

    # Step 4: Pass valid cars to persistence layer
    # See persistence.md for DatabaseSaver usage
    return validation_result.valid_cars
```

---

## 🐛 Troubleshooting

### High Parsing Error Rate
**Symptoms**: Many `ParsingError` exceptions
**Cause**: encar.com page structure changed
**Solution**:
```python
# Enable debug mode to see parsing details
parser = CarParser(debug_mode=True)
await parser.debug_page_structure("https://encar.com/car/123456")
```

### Validation Failures
**Symptoms**: Most cars fail validation
**Cause**: New data formats or business rule changes
**Solution**:
```python
# Analyze validation errors
validation_result = await validator.validate_batch(raw_cars)
error_summary = validator.analyze_errors(validation_result.validation_errors)
print(error_summary.most_common_errors)
```

**Next**: See [persistence.md](./persistence.md) for DatabaseSaver and NotificationService
```

### persistence.md Example (Abbreviated)
```markdown
# 💾 Persistence: Storage & Notifications

## 🎯 Quick Summary
Documentation for DatabaseSaver and NotificationService - handles data persistence, deduplication, and admin notifications.

## 📋 Table of Contents
1. [DatabaseSaver Module](#databasesaver-module)
2. [NotificationService Module](#notificationservice-module)
3. [Integration with Data Processing](#integration-with-data-processing)

## 🔑 Modules in This File
- **DatabaseSaver**: PostgreSQL operations with deduplication
- **NotificationService**: Email alerts and monitoring

---

## 💾 DatabaseSaver Module

### Purpose
Handles car data persistence to PostgreSQL with automatic deduplication and performance optimization.

```python
from car_import_system import DatabaseSaver
from car_import_system.models import SaveResult

# Initialize with database connection
saver = DatabaseSaver(connection_string="postgresql://...")

# Save validated cars (from data-processing.md)
valid_cars = await validation_result.valid_cars
save_result = await saver.save_cars_batch(valid_cars)

print(f"Saved: {save_result.cars_added}")
print(f"Duplicates skipped: {save_result.duplicates_skipped}")
print(f"Errors: {save_result.save_errors}")
```

---

## 📧 NotificationService Module

### Purpose
Sends email notifications for import status, errors, and system monitoring.

```python
from car_import_system import NotificationService

notifier = NotificationService(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    username="system@company.com",
    password="app_password"
)

# Send import completion notification
await notifier.send_import_summary(
    cars_imported=1250,
    errors=15,
    duration_minutes=45,
    recipients=["admin@company.com"]
)
```

**Previous**: See [data-processing.md](./data-processing.md) for CarParser and DataValidator
```

---

## ✅ Quality Checklist

### File Organization Check
- [ ] **2-3 files** focused on logical boundaries
- [ ] **index.md** provides clear navigation and overview
- [ ] **Specialized files** cover related functionality deeply
- [ ] **File sizes** < 1000 lines each
- [ ] **Cross-references** help navigate between files

### Content Quality Check
- [ ] **Overview** in index.md explains system purpose
- [ ] **Quick start** works end-to-end
- [ ] **Detailed files** provide comprehensive coverage
- [ ] **Integration patterns** show how modules work together
- [ ] **Troubleshooting** covers common issues across files

### User Experience Check
- [ ] New developer can understand system in 5 minutes
- [ ] They can find specific information in <15 seconds
- [ ] They can run working examples from any file
- [ ] They understand how components connect
- [ ] They know where to look for specific problems

### AI Optimization Check
- [ ] Clear section headers in all files
- [ ] Consistent markdown formatting
- [ ] Type-safe examples with Pydantic models
- [ ] No raw dict/Any usage
- [ ] Metadata and tags for searchability

**Time Investment**: 2-4 hours for comprehensive multi-module documentation
**Result**: Cohesive documentation system that covers related functionality comprehensively while maintaining AI-friendly structure
