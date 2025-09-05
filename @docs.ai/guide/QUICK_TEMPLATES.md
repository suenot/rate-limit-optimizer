# ⚡ Quick Templates & Copy-Paste Examples

## 🎯 Quick Summary
Ready-to-use templates for common documentation scenarios. Copy, modify, and use immediately for faster documentation creation.

## 📋 Table of Contents
1. [Python Module Templates](#python-module-templates)
2. [API Documentation Templates](#api-documentation-templates)
3. [React Component Templates](#react-component-templates)
4. [Database Model Templates](#database-model-templates)
5. [Workflow/Flow Templates](#workflowflow-templates)
6. [Integration Templates](#integration-templates)

## 🔑 Template Categories at a Glance
- **Python modules**: Classes, services, utilities
- **API endpoints**: REST, GraphQL, WebSocket
- **Frontend components**: React, Vue, Angular
- **Data models**: Database, Pydantic, TypeScript
- **Workflows**: Business processes, technical flows
- **Integrations**: External APIs, webhooks, queues

---

## 🐍 Python Module Templates

### Python Class Template
```markdown
# 📦 Module: [ClassName]

## 🎯 Quick Summary
- [What this class does in 1-2 sentences]
- [Primary use cases and responsibilities]

## 📋 Table of Contents
1. [Purpose](#purpose)
2. [Quick Start](#quick-start)
3. [API Reference](#api-reference)
4. [Examples](#examples)
5. [Integration](#integration)
6. [Common Mistakes](#common-mistakes)

## 🔑 Key Concepts at a Glance
- **Main Methods**: [method1, method2, method3]
- **Dependencies**: [dep1, dep2]
- **Return Types**: [Primary return types]
- **Thread Safety**: [Yes/No + details]

## 🚀 Quick Start

```python
from [module] import [ClassName]

# Basic usage
instance = [ClassName](param1="value")
result = await instance.main_method()
print(result)
```

## 📊 API Reference

### class [ClassName](BaseClass)
[Purpose and main responsibilities]

#### __init__(param1: Type, param2: Type = default)
Initialize [ClassName] with configuration.

**Parameters**:
- `param1` (Type): [Description]
- `param2` (Type, optional): [Description] (default: value)

#### async main_method(input_data: InputType) -> OutputType
[Method description and purpose]

**Parameters**:
- `input_data` (InputType): [Description]

**Returns**: OutputType with [description]

**Raises**:
- `CustomError`: When [condition]
- `ValueError`: When [condition]

```python
# Example usage
result = await instance.main_method(input_data)
assert isinstance(result, OutputType)
```

## 💡 Usage Examples

### Basic Operations
```python
# Initialize with custom config
config = Config(timeout=30, retries=3)
processor = [ClassName](config)

# Process single item
item = {"key": "value"}
result = await processor.process_item(item)
print(f"Processed: {result.status}")
```

### Batch Processing
```python
# Process multiple items
items = [{"id": 1}, {"id": 2}, {"id": 3}]
results = await processor.process_batch(items)

for result in results:
    if result.success:
        print(f"Success: {result.data}")
    else:
        print(f"Error: {result.error}")
```

### Error Handling
```python
try:
    result = await processor.process_item(item)
except ProcessingError as e:
    logger.error(f"Processing failed: {e.details}")
    # Handle specific error
except ValidationError as e:
    logger.error(f"Invalid input: {e.errors}")
    # Handle validation error
```

## 🔗 Integration

### With Other Modules
```python
# Use with [RelatedModule]
from [related_module] import [RelatedClass]

processor = [ClassName](config)
validator = [RelatedClass]()

# Integration pattern
validated_data = await validator.validate(raw_data)
result = await processor.process_item(validated_data)
```

### With Database
```python
from database.models import [ModelName]

# Save results to database
result = await processor.process_item(item)
await [ModelName].objects.create(**result.dict())
```

## ❌ Common Mistakes

### Mistake 1: [Common Error]
**Problem**: [What goes wrong]
```python
# ❌ WRONG
instance = [ClassName]()  # Missing required config
```
**Solution**: [How to fix it]
```python
# ✅ CORRECT
config = Config(required_param="value")
instance = [ClassName](config)
```

### Mistake 2: [Another Error]
**Problem**: [What goes wrong]
**Solution**: [How to fix it]

## 🐛 Troubleshooting

### Issue: [Common Problem]
**Symptoms**: [How it manifests]
**Cause**: [Why it happens]
**Solution**: [How to fix]

## 🏷️ Metadata
**Tags**: [relevant, tags, here]
**Added in**: v1.0
**Dependencies**: [dep1>=1.0, dep2>=2.0]
**Used by**: [module1, module2]
```

### Python Service Template
```markdown
# 🔧 Service: [ServiceName]

## 🎯 Quick Summary
- [Service purpose and business value]
- [Key operations and responsibilities]

## 🔑 Key Concepts
- **Main Operations**: [operation1, operation2]
- **Dependencies**: [external services, databases]
- **Return Types**: [Pydantic models used]
- **Error Handling**: [Custom exceptions]

## 🚀 Quick Start
```python
from services.[service_name] import [ServiceName]
from models.[model_name] import [ModelName]

service = [ServiceName](config)
result = await service.main_operation(input_data)
```

## 📊 Operations

### async main_operation(input: InputModel) -> OutputModel
[Operation description]

### async batch_operation(items: List[InputModel]) -> List[OutputModel]
[Batch operation description]

[Rest of template structure similar to class template...]
```

---

## 🔌 API Documentation Templates

### REST API Endpoint Template
```markdown
# 🔌 API: [Endpoint Name]

## 🎯 Quick Summary
- [What this endpoint does]
- [Primary use cases]

## 📋 Endpoints
1. [GET /endpoint](#get-endpoint)
2. [POST /endpoint](#post-endpoint)
3. [PUT /endpoint/{id}](#put-endpoint)
4. [DELETE /endpoint/{id}](#delete-endpoint)

## 🔑 Key Information
- **Base URL**: `https://api.example.com/v1`
- **Authentication**: Bearer token required
- **Rate Limiting**: 1000 requests/hour
- **Response Format**: JSON

## 📊 API Reference

### GET /api/[resource]
Retrieve [resource] list with filtering and pagination.

**Parameters**:
- `page` (integer, optional): Page number (default: 1)
- `limit` (integer, optional): Items per page (default: 20, max: 100)
- `filter_field` (string, optional): Filter by [description]

**Headers**:
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Response** (200):
```json
{
  "data": [
    {
      "id": 123,
      "field1": "value1",
      "field2": "value2",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

**Error Response** (400):
```json
{
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Invalid page parameter",
    "details": {
      "parameter": "page",
      "provided": -1,
      "expected": "positive integer"
    }
  }
}
```

### POST /api/[resource]
Create new [resource].

**Request Body**:
```json
{
  "field1": "value1",
  "field2": "value2",
  "optional_field": "optional_value"
}
```

**Response** (201):
```json
{
  "id": 124,
  "field1": "value1",
  "field2": "value2",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## 💡 Usage Examples

### JavaScript/TypeScript
```typescript
// Fetch resources
const response = await fetch('/api/[resource]?page=1&limit=10', {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});
const data = await response.json();

// Create new resource
const newResource = await fetch('/api/[resource]', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    field1: 'value1',
    field2: 'value2'
  })
});
```

### Python
```python
import aiohttp

async def get_resources(page=1, limit=20):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f'/api/[resource]?page={page}&limit={limit}',
            headers=headers
        ) as response:
            return await response.json()

async def create_resource(data):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            '/api/[resource]',
            headers=headers,
            json=data
        ) as response:
            return await response.json()
```

## ❌ Common Errors

### 401 Unauthorized
**Cause**: Missing or invalid access token
**Solution**: Ensure valid Bearer token in Authorization header

### 429 Rate Limited
**Cause**: Too many requests
**Solution**: Implement exponential backoff, respect rate limits

### 422 Validation Error
**Cause**: Invalid request data
**Solution**: Check required fields and data types

## 🏷️ Metadata
**Version**: v1.0
**Authentication**: Required
**Rate Limits**: 1000/hour
**Last Updated**: [Date]
```

---

## ⚛️ React Component Templates

### React Component Template
```markdown
# ⚛️ Component: [ComponentName]

## 🎯 Quick Summary
- [Component purpose and UI responsibility]
- [Key features and behavior]

## 🔑 Key Properties
- **Props**: [main props and their types]
- **State**: [internal state if complex]
- **Events**: [callback props]
- **Styling**: [CSS modules/styled-components/etc]

## 🚀 Quick Start
```tsx
import { [ComponentName] } from './components/[ComponentName]';

function App() {
  return (
    <[ComponentName]
      prop1="value1"
      prop2={value2}
      onEvent={handleEvent}
    />
  );
}
```

## 📊 Props Interface
```typescript
interface [ComponentName]Props {
  // Required props
  prop1: string;
  prop2: number;

  // Optional props
  prop3?: boolean;
  prop4?: CustomType;

  // Event handlers
  onEvent?: (data: EventData) => void;
  onChange?: (value: string) => void;

  // Styling
  className?: string;
  style?: React.CSSProperties;

  // Children
  children?: React.ReactNode;
}
```

## 💡 Usage Examples

### Basic Usage
```tsx
import { [ComponentName] } from './components/[ComponentName]';

function BasicExample() {
  const handleEvent = (data: EventData) => {
    console.log('Event received:', data);
  };

  return (
    <[ComponentName]
      prop1="example value"
      prop2={42}
      onEvent={handleEvent}
    />
  );
}
```

### Advanced Usage with State
```tsx
import { useState } from 'react';
import { [ComponentName] } from './components/[ComponentName]';

function AdvancedExample() {
  const [value, setValue] = useState('');
  const [isEnabled, setIsEnabled] = useState(true);

  return (
    <[ComponentName]
      prop1={value}
      prop2={isEnabled ? 1 : 0}
      onChange={setValue}
      onEvent={(data) => {
        if (data.type === 'success') {
          setIsEnabled(true);
        }
      }}
    />
  );
}
```

### With Custom Styling
```tsx
import styles from './[ComponentName].module.css';

function StyledExample() {
  return (
    <[ComponentName]
      prop1="styled example"
      className={styles.customStyle}
      style={{ marginTop: 20 }}
    />
  );
}
```

## 🎨 Styling

### CSS Modules
```css
/* [ComponentName].module.css */
.container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.title {
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--primary-color);
}

.content {
  flex: 1;
  padding: 1rem;
  background: var(--background-color);
  border-radius: 0.5rem;
}
```

### Styled Components
```tsx
import styled from 'styled-components';

const Container = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const Title = styled.h2`
  font-size: 1.5rem;
  font-weight: bold;
  color: ${props => props.theme.primary};
`;
```

## 🔗 Integration

### With Form Libraries
```tsx
import { useForm } from 'react-hook-form';

function FormExample() {
  const { register, handleSubmit } = useForm();

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <[ComponentName]
        {...register('fieldName')}
        prop1="form field"
      />
    </form>
  );
}
```

### With State Management
```tsx
import { useSelector, useDispatch } from 'react-redux';

function ReduxExample() {
  const data = useSelector(state => state.[slice].[field]);
  const dispatch = useDispatch();

  return (
    <[ComponentName]
      prop1={data}
      onEvent={(data) => dispatch(actionCreator(data))}
    />
  );
}
```

## ❌ Common Mistakes

### Mistake 1: [Common React Error]
**Problem**: [Description]
```tsx
// ❌ WRONG
<[ComponentName] prop1={undefined} />
```
**Solution**: [How to fix]
```tsx
// ✅ CORRECT
<[ComponentName] prop1="default value" />
```

## 🧪 Testing

### Unit Tests
```tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { [ComponentName] } from './[ComponentName]';

describe('[ComponentName]', () => {
  it('renders with required props', () => {
    render(<[ComponentName] prop1="test" prop2={1} />);
    expect(screen.getByText('test')).toBeInTheDocument();
  });

  it('calls event handler when interacted', () => {
    const mockHandler = jest.fn();
    render(
      <[ComponentName]
        prop1="test"
        prop2={1}
        onEvent={mockHandler}
      />
    );

    fireEvent.click(screen.getByRole('button'));
    expect(mockHandler).toHaveBeenCalledWith(expect.any(Object));
  });
});
```

## 🏷️ Metadata
**Type**: React Component
**Category**: [UI Category]
**Dependencies**: [dependencies]
**Browser Support**: Modern browsers
```

---

## 🗄️ Database Model Templates

### Pydantic Model Template
```markdown
# 📊 Model: [ModelName]

## 🎯 Quick Summary
- [Data model purpose and business domain]
- [Key relationships and constraints]

## 🔑 Key Information
- **Table**: [table_name]
- **Primary Key**: [field_name]
- **Relationships**: [related models]
- **Validation Rules**: [business rules]

## 📊 Model Definition

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

class [ModelName]Status(str, Enum):
    """Status enumeration for [ModelName]."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    DELETED = "deleted"

class [ModelName](BaseModel):
    """[Description of what this model represents]."""

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "field1": "example_value",
                "field2": 123,
                "status": "active"
            }
        }
    )

    # Primary fields
    id: int = Field(..., gt=0, description="Unique identifier")
    field1: str = Field(..., min_length=1, max_length=100, description="Field description")
    field2: int = Field(..., ge=0, description="Field description")

    # Optional fields
    optional_field: Optional[str] = Field(None, max_length=500)

    # Enum fields
    status: [ModelName]Status = Field(default=[ModelName]Status.ACTIVE)

    # Decimal fields
    amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)

    # Date fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(None)

    # List fields
    tags: List[str] = Field(default_factory=list, max_items=10)

    @validator('field1')
    def validate_field1(cls, v):
        """Custom validation for field1."""
        return v.strip().lower()

    @validator('amount')
    def validate_amount(cls, v, values):
        """Cross-field validation example."""
        status = values.get('status')
        if status == [ModelName]Status.ACTIVE and v is None:
            raise ValueError('Amount required for active records')
        return v

    @property
    def display_name(self) -> str:
        """Computed property for display."""
        return f"{self.field1} ({self.id})"
```

## 📋 Related Models

### Create/Update Models
```python
class [ModelName]Create(BaseModel):
    """Model for creating new [ModelName] records."""
    field1: str = Field(..., min_length=1, max_length=100)
    field2: int = Field(..., ge=0)
    optional_field: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class [ModelName]Update(BaseModel):
    """Model for updating existing [ModelName] records."""
    field1: Optional[str] = Field(None, min_length=1, max_length=100)
    field2: Optional[int] = Field(None, ge=0)
    optional_field: Optional[str] = None
    status: Optional[[ModelName]Status] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class [ModelName]Response(BaseModel):
    """Model for API responses."""
    id: int
    field1: str
    field2: int
    status: [ModelName]Status
    created_at: datetime
    display_name: str
```

## 💡 Usage Examples

### Basic Operations
```python
# Create new record
create_data = [ModelName]Create(
    field1="example",
    field2=42,
    tags=["tag1", "tag2"]
)

# Validate and create model
new_model = [ModelName](
    id=1,
    **create_data.dict()
)

print(f"Created: {new_model.display_name}")
```

### Database Integration
```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class [ModelName]Table(Base):
    """SQLAlchemy table for [ModelName]."""
    __tablename__ = '[table_name]'

    id = Column(Integer, primary_key=True)
    field1 = Column(String(100), nullable=False)
    field2 = Column(Integer, nullable=False)
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)

# Convert between Pydantic and SQLAlchemy
def to_pydantic(db_record: [ModelName]Table) -> [ModelName]:
    return [ModelName](
        id=db_record.id,
        field1=db_record.field1,
        field2=db_record.field2,
        status=db_record.status,
        created_at=db_record.created_at
    )
```

### API Integration
```python
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.post("/[model_name]/", response_model=[ModelName]Response)
async def create_model(data: [ModelName]Create):
    """Create new [ModelName] record."""
    try:
        # Validate input
        model = [ModelName](id=generate_id(), **data.dict())

        # Save to database
        saved_model = await save_to_db(model)

        # Return response
        return [ModelName]Response(**saved_model.dict())

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=e.errors())
```

## ❌ Common Validation Errors

### Error 1: [Common Issue]
**Problem**: [Description]
**Solution**: [How to fix]

### Error 2: [Another Issue]
**Problem**: [Description]
**Solution**: [How to fix]

## 🏷️ Metadata
**Domain**: [Business Domain]
**Table**: [database_table]
**Version**: v1.0
**Relationships**: [related_models]
```

---

## 🔄 Workflow/Flow Templates

### Business Process Flow Template
```markdown
# 🔄 Flow: [Process Name]

## 🎯 Quick Summary
- [What business process this documents]
- [Key participants and outcomes]

## 📋 Table of Contents
1. [Flow Overview](#flow-overview)
2. [Step-by-Step Process](#step-by-step-process)
3. [Systems Involved](#systems-involved)
4. [Error Scenarios](#error-scenarios)
5. [Monitoring Points](#monitoring-points)

## 🔑 Key Information
- **Duration**: [Typical process duration]
- **Participants**: [User roles involved]
- **Systems**: [Technical systems involved]
- **Triggers**: [What starts this process]

## 🔄 Flow Overview

```
[Start] → [Step 1] → [Step 2] → [Decision] → [Step 3] → [End]
            ↓           ↓          ↓          ↓
         [System A]  [System B]  [Logic]   [System C]
```

## 📝 Step-by-Step Process

### Step 1: [Initial Action]
**Participant**: [Who performs this]
**System**: [Technical system involved]
**Duration**: [Typical time]

**Actions**:
1. [Specific action 1]
2. [Specific action 2]
3. [Specific action 3]

**Code Example**:
```python
# Step 1 implementation
result = await system_a.perform_action(input_data)
if result.success:
    proceed_to_step_2(result.data)
else:
    handle_error(result.error)
```

**Data Flow**:
- **Input**: [InputDataType]
- **Output**: [OutputDataType]
- **Side Effects**: [What changes in the system]

### Step 2: [Next Action]
**Participant**: [Who performs this]
**System**: [Technical system involved]
**Duration**: [Typical time]

[Similar structure for each step...]

### Decision Point: [Business Logic]
**Criteria**: [How decision is made]
**Outcomes**:
- **Path A**: [Condition] → Go to [Step X]
- **Path B**: [Condition] → Go to [Step Y]
- **Error**: [Error condition] → Go to [Error Handler]

## 🖥️ Systems Involved

### [System Name 1]
**Role**: [What this system does in the flow]
**Operations**: [Specific operations used]
**Documentation**: [Link to system docs]

### [System Name 2]
**Role**: [What this system does in the flow]
**Operations**: [Specific operations used]
**Documentation**: [Link to system docs]

## ❌ Error Scenarios

### Error 1: [Common Failure]
**Symptoms**: [How to identify]
**Cause**: [Why it happens]
**Impact**: [Effect on process]
**Resolution**: [How to fix]
**Prevention**: [How to avoid]

### Error 2: [Another Failure]
[Similar structure...]

## 📊 Monitoring Points

### Key Metrics
- **Success Rate**: [Target percentage]
- **Processing Time**: [Target duration]
- **Error Rate**: [Maximum acceptable]
- **Throughput**: [Volume targets]

### Alerts
- **Critical**: [When to alert immediately]
- **Warning**: [When to flag for attention]
- **Info**: [Normal operational notifications]

## 🏷️ Metadata
**Process Type**: [Business/Technical/Hybrid]
**Frequency**: [How often this runs]
**Criticality**: [High/Medium/Low]
**Owner**: [Team responsible]
```

---

## 🔗 Integration Templates

### External API Integration Template
```markdown
# 🔗 Integration: [External Service Name]

## 🎯 Quick Summary
- [What external service this integrates with]
- [Business value and use cases]

## 🔑 Integration Details
- **Service**: [External service name]
- **Protocol**: [REST/GraphQL/WebSocket/etc]
- **Authentication**: [API key/OAuth/etc]
- **Rate Limits**: [Requests per hour/minute]
- **Documentation**: [Link to external docs]

## 🚀 Quick Start

```python
from integrations.[service_name] import [ServiceName]Client
from models.integrations import [ServiceName]Config

# Initialize client
config = [ServiceName]Config(
    api_key="your_api_key",
    base_url="https://api.[service].com/v1",
    timeout_seconds=30
)

client = [ServiceName]Client(config)

# Basic operation
result = await client.get_data(query_params)
print(result)
```

## 📊 Available Operations

### get_[resource](params: QueryParams) -> [Resource]Response
[Description of what this operation does]

**Parameters**:
- `params` ([QueryParams]): [Description]

**Returns**: [Resource]Response with [description]

**Example**:
```python
params = QueryParams(
    field1="value1",
    limit=50
)
response = await client.get_[resource](params)
```

### create_[resource](data: [Resource]Create) -> [Resource]Response
[Description of creation operation]

**Parameters**:
- `data` ([Resource]Create): [Description]

**Example**:
```python
create_data = [Resource]Create(
    name="Example",
    description="Test resource"
)
response = await client.create_[resource](create_data)
```

## 🔄 Webhook Handling

### Webhook Events
```python
from fastapi import APIRouter, Request
from integrations.[service_name] import verify_webhook

router = APIRouter()

@router.post("/webhooks/[service_name]")
async def handle_webhook(request: Request):
    """Handle incoming webhooks from [service_name]."""

    # Verify webhook signature
    signature = request.headers.get("X-[Service]-Signature")
    payload = await request.body()

    if not verify_webhook(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Process webhook data
    webhook_data = await request.json()
    await process_webhook_event(webhook_data)

    return {"status": "success"}

async def process_webhook_event(data: dict):
    """Process specific webhook events."""
    event_type = data.get("type")

    if event_type == "resource.created":
        await handle_resource_created(data["data"])
    elif event_type == "resource.updated":
        await handle_resource_updated(data["data"])
    elif event_type == "resource.deleted":
        await handle_resource_deleted(data["data"])
```

## ❌ Error Handling

### Rate Limiting
```python
import asyncio
from datetime import datetime, timedelta

class RateLimitHandler:
    def __init__(self):
        self.last_request = datetime.now()
        self.request_count = 0

    async def wait_if_needed(self):
        """Implement rate limiting logic."""
        now = datetime.now()
        if now - self.last_request < timedelta(seconds=1):
            await asyncio.sleep(1)
        self.last_request = now

# Usage
rate_limiter = RateLimitHandler()

async def make_api_request():
    await rate_limiter.wait_if_needed()
    return await client.get_data()
```

### Retry Logic
```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def resilient_api_call(params):
    """API call with automatic retry."""
    try:
        return await client.get_data(params)
    except RateLimitError:
        await asyncio.sleep(60)  # Wait before retry
        raise
    except NetworkError as e:
        logger.warning(f"Network error, retrying: {e}")
        raise
```

## 🧪 Testing

### Mock Integration
```python
import pytest
from unittest.mock import AsyncMock
from integrations.[service_name] import [ServiceName]Client

@pytest.fixture
def mock_client():
    """Mock client for testing."""
    client = AsyncMock(spec=[ServiceName]Client)
    client.get_data.return_value = MockResponse(
        data=[{"id": 1, "name": "test"}],
        status="success"
    )
    return client

@pytest.mark.asyncio
async def test_integration(mock_client):
    """Test integration logic with mocked client."""
    result = await mock_client.get_data({"query": "test"})
    assert result.status == "success"
    assert len(result.data) == 1
```

## 🏷️ Metadata
**Service Provider**: [Company/Organization]
**API Version**: [Version number]
**Rate Limits**: [Specific limits]
**SLA**: [Service level agreement]
**Support**: [How to get help]
```

---

## ✅ Quick Selection Guide

### Choose Template by Use Case

**Python Code**:
- Class/Service → Python Module Template
- Data structures → Database Model Template

**APIs**:
- REST endpoints → REST API Template
- External services → Integration Template

**Frontend**:
- UI components → React Component Template
- Pages/features → Workflow Template

**Processes**:
- Business logic → Workflow Template
- Technical flows → Integration Template

### Customization Tips

1. **Replace placeholders**: [Brackets] with actual names
2. **Adapt sections**: Add/remove based on complexity
3. **Update examples**: Use real domain data
4. **Adjust metadata**: Tags, versions, dependencies
5. **Cross-reference**: Link to related documentation

**Time Savings**: These templates reduce documentation time by 60-80% while ensuring consistency and completeness.
