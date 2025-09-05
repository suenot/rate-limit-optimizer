# 🔌 Auto-Generated SDK + Service Layer Patterns %%PRIORITY:HIGH%%

## 🎯 Quick Summary
Patterns for Next.js applications using **auto-generated TypeScript SDK** from OpenAPI with custom **Service Layer** on top. Perfect for projects where backend generates OpenAPI schema and frontend SDK is auto-generated.

## 📋 Table of Contents
1. [Generated SDK Architecture](#generated-sdk-architecture)
2. [Service Layer Over SDK](#service-layer-over-sdk)
3. [Type Safety with Generated Types](#type-safety-with-generated-types)
4. [BaseService Pattern](#baseservice-pattern)
5. [Business Logic Layer](#business-logic-layer)
6. [Integration with React](#integration-with-react)

## 🔑 Key Architecture at a Glance
- **Auto-Generated SDK**: TypeScript client generated from OpenAPI schema
- **Service Layer**: Business logic and convenience methods over raw SDK
- **Type Proxy**: Clean type imports through re-export files
- **BaseService**: Common error handling and response processing
- **Business Methods**: High-level operations with sensible defaults
- **React Integration**: Simple, clean component usage

---

## 🏗️ Generated SDK Architecture

### Project Structure with Auto-Generated SDK
```
src/
├── apiServer/
│   ├── sdk_generated/              # 🤖 AUTO-GENERATED - DO NOT EDIT
│   │   ├── typescript_http/
│   │   │   ├── api.ts              # Generated API client
│   │   │   └── types.gen.ts        # Generated TypeScript types
│   │   ├── typescript_websocket/
│   │   │   └── client.ts           # Generated WebSocket client
│   │   └── openapi.yaml            # Source OpenAPI schema
│   ├── services/                   # 🎯 YOUR CODE - Business logic
│   │   ├── BaseService.ts          # Common patterns and error handling
│   │   ├── AdminService.ts         # Admin operations
│   │   ├── UserService.ts          # User management
│   │   ├── ParserService.ts        # Parser operations
│   │   ├── types/                  # Type re-exports for clean imports
│   │   │   ├── admin.ts            # Admin types proxy
│   │   │   ├── user.ts             # User types proxy
│   │   │   └── parser.ts           # Parser types proxy
│   │   └── index.ts                # Service exports
│   └── client.ts                   # API client configuration
```

### Key Architecture Principles

#### 1. **Generated SDK** (sdk_generated/) - Never Touch
```typescript
// sdk_generated/typescript_http/api.ts - GENERATED, DON'T EDIT
export class ApiClient {
  // Auto-generated methods with long names
  async broadcastMessageApiV1AdminBroadcastPost(params: {
    body: BroadcastMessageRequest;
  }): Promise<{ data: BroadcastResultResponse }> {
    // Generated implementation
  }

  async getUsersApiV1UsersGet(): Promise<{ data: UserListResponse }> {
    // Generated implementation
  }
}
```

#### 2. **Service Layer** (services/) - Your Business Logic
```typescript
// services/AdminService.ts - YOUR CODE
export class AdminService extends BaseService {
  // Simple, human-readable method names
  static async sendSystemNotification(message: string, priority = 'normal') {
    return this.client.api.broadcastMessageApiV1AdminBroadcastPost({
      body: {
        message,
        priority,
        target: 'all_users',
        persistent: true,
      }
    });
  }
}
```

---

## 🔧 BaseService Pattern

### BaseService Implementation
```typescript
// services/BaseService.ts
import api from '../client';
import type {
  SuccessResponse,
  ErrorResponse,
} from '../sdk_generated/typescript_http/types.gen';

/**
 * Base service class with common functionality for all API services
 */
export abstract class BaseService {
  protected static client = api; // Shared API client instance

  /**
   * Handle API response and extract data
   * All generated SDK methods return { data: T } format
   */
  protected static handleResponse<T>(response: unknown): T {
    if (!response) {
      throw new Error('No response received from API');
    }

    // Handle success response format { success: boolean, data: T }
    if (typeof response === 'object' && response !== null && 'success' in response) {
      const successResponse = response as SuccessResponse;
      if (successResponse.success === false) {
        throw new Error(
          typeof successResponse.message === 'string'
            ? successResponse.message
            : 'API request failed'
        );
      }
      return successResponse.data as T;
    }

    // Handle direct data response
    return response as T;
  }

  /**
   * Handle API errors consistently
   */
  protected static handleError(error: unknown): never {
    if (error && typeof error === 'object' && 'response' in error) {
      const httpError = error as { response?: { data?: ErrorResponse } };
      if (httpError.response?.data) {
        const errorData = httpError.response.data;
        throw new Error(
          typeof errorData.message === 'string'
            ? errorData.message
            : 'API request failed'
        );
      }
    }

    if (error instanceof Error) {
      throw new Error(error.message);
    }

    throw new Error('Unknown API error occurred');
  }

  /**
   * Safe API call with consistent error handling
   * Use for wrapping generated SDK calls
   */
  protected static async safeApiCall<T>(apiCall: () => Promise<unknown>): Promise<T> {
    try {
      const response = await apiCall();
      return this.handleResponse<T>(response);
    } catch (error) {
      this.handleError(error);
    }
  }
}

### Client Configuration
```typescript
// client.ts - API client setup
import { ApiClient } from './sdk_generated/typescript_http/api';

// Initialize the API client with base URL
const api = new ApiClient('http://localhost:8000');

export default api;
export { api };

// Re-export useful constants from generated SDK
export { TOKEN_KEY, REFRESH_TOKEN_KEY } from './sdk_generated/typescript_http/api';
```

---

## 🏗️ Service Layer Over SDK

### Domain Service Implementation

#### Admin Service Example
```typescript
// services/AdminService.ts
import { BaseService } from './BaseService';
import type { BroadcastMessageRequest, MaintenanceModeRequest } from './types/admin';

/**
 * Admin Service for system administration and management
 * Wraps generated SDK methods with business logic
 */
export class AdminService extends BaseService {
  /**
   * Low-level method: Direct SDK wrapper
   */
  static async broadcastMessage(message: BroadcastMessageRequest) {
    const response = await this.client.api.broadcastMessageApiV1AdminBroadcastPost({
      body: message,
    });
    if (!response.data) {
      throw new Error('Failed to broadcast message');
    }
    return response.data;
  }

  /**
   * High-level method: Business logic with defaults
   */
  static async sendSystemNotification(
    message: string,
    title?: string,
    priority: 'low' | 'normal' | 'high' | 'urgent' | 'critical' = 'normal'
  ) {
    return this.broadcastMessage({
      message,
      title,
      priority,
      target: 'all_users',     // Sensible default
      persistent: true,        // Always persistent for system messages
    });
  }

  /**
   * Convenience method: Specific use case
   */
  static async sendAdminAlert(message: string, priority: 'urgent' | 'critical' = 'urgent') {
    return this.broadcastMessage({
      message,
      title: 'Admin Alert',
      priority,
      target: 'admins_only',   // Only to admins
      persistent: true,
    });
  }

  /**
   * Maintenance mode management
   */
  static async enableMaintenanceMode(
    reason: string,
    estimatedDurationMinutes?: number,
    gracePeriodMinutes?: number
  ) {
    return this.manageMaintenanceMode({
      enable: true,
      reason,
      estimated_duration_minutes: estimatedDurationMinutes,
      grace_period_minutes: gracePeriodMinutes || 5, // Default grace period
      notify_users: true, // Always notify users
    });
  }

  static async disableMaintenanceMode() {
    return this.manageMaintenanceMode({
      enable: false,
      reason: 'Maintenance completed',
      notify_users: true,
    });
  }

  /**
   * Utility method: Simple status check
   */
  static async isMaintenanceMode(): Promise<boolean> {
    try {
      const status = await this.getMaintenanceStatus();
      return status.maintenance_active;
    } catch (error) {
      console.warn('Failed to check maintenance status:', error);
      return false; // Fail gracefully
    }
  }

  // Private method: Raw SDK call
  private static async manageMaintenanceMode(request: MaintenanceModeRequest) {
    const response = await this.client.api.manageMaintenanceModeApiV1AdminMaintenancePost({
      body: request,
    });
    if (!response.data) {
      throw new Error('Failed to manage maintenance mode');
    }
    return response.data;
  }

  private static async getMaintenanceStatus() {
    const response = await this.client.api.getMaintenanceStatusApiV1AdminMaintenanceStatusGet();
    if (!response.data) {
      throw new Error('Failed to get maintenance status');
    }
    return response.data;
  }
}
```

#### User Service Example
```typescript
// services/UserService.ts
export class UserService extends BaseService {
  /**
   * Get paginated users list
   */
  static async getUsers(params?: {
    page?: number;
    limit?: number;
    search?: string;
    role?: UserRole;
  }) {
    const response = await this.client.api.getUsersApiV1UsersGet({
      query: {
        page: params?.page || 1,
        limit: params?.limit || 20,
        search: params?.search,
        role: params?.role,
      }
    });
    if (!response.data) {
      throw new Error('Failed to get users');
    }
    return response.data;
  }

  /**
   * Get single user by ID
   */
  static async getUser(userId: string) {
    const response = await this.client.api.getUserApiV1UsersUserIdGet({
      path: { user_id: userId }
    });
    if (!response.data) {
      throw new Error('Failed to get user');
    }
    return response.data;
  }

  /**
   * Create new user with validation
   */
  static async createUser(userData: CreateUserRequest) {
    // Business logic: validate email format
    if (!userData.email.includes('@')) {
      throw new Error('Invalid email format');
    }

    const response = await this.client.api.createUserApiV1UsersPost({
      body: userData
    });
    if (!response.data) {
      throw new Error('Failed to create user');
    }
    return response.data;
  }

  /**
   * Bulk operations: Multiple users
   */
  static async bulkUpdateUsers(updates: Array<{ id: string; updates: UpdateUserRequest }>) {
    const promises = updates.map(({ id, updates }) =>
      this.updateUser(id, updates)
    );
    return Promise.all(promises);
  }

  private static async updateUser(userId: string, updates: UpdateUserRequest) {
    const response = await this.client.api.updateUserApiV1UsersUserIdPut({
      path: { user_id: userId },
      body: updates
    });
    if (!response.data) {
      throw new Error('Failed to update user');
    }
    return response.data;
  }
}
```

---

## 🎯 Type Safety with Generated Types

### Type Proxy Pattern

#### Clean Type Imports with Re-exports
```typescript
// services/types/admin.ts - Type proxy for clean imports
import type {
  // Broadcast types from generated SDK
  BroadcastMessageRequest,
  BroadcastResultResponse,
  BroadcastDeliveryStats,
  BroadcastPriority,
  BroadcastTarget,

  // Maintenance types
  MaintenanceModeRequest,
  MaintenanceStatusResponse,
  MaintenanceMode,

  // Service stats
  ServiceStatsResponse,

  // Common response types
  SuccessResponse,
  ErrorResponse,
} from '../../sdk_generated/typescript_http/types.gen';

// Re-export all types for clean imports
export type {
  // Broadcast types
  BroadcastMessageRequest,
  BroadcastResultResponse,
  BroadcastDeliveryStats,
  BroadcastPriority,
  BroadcastTarget,

  // Maintenance types
  MaintenanceModeRequest,
  MaintenanceStatusResponse,
  MaintenanceMode,

  // Service stats
  ServiceStatsResponse,

  // Common response types
  SuccessResponse,
  ErrorResponse,
};

// Additional custom types for enhanced functionality
export type NotificationRequest = {
  message: string;
  title?: string;
  priority?: 'low' | 'normal' | 'high' | 'urgent' | 'critical';
};
```

#### User Types Proxy
```typescript
// services/types/user.ts
import type {
  User,
  UserRole,
  UserStatus,
  CreateUserRequest,
  UpdateUserRequest,
  UserListResponse,
  PaginationMeta,
} from '../../sdk_generated/typescript_http/types.gen';

// Re-export generated types
export type {
  User,
  UserRole,
  UserStatus,
  CreateUserRequest,
  UpdateUserRequest,
  UserListResponse,
  PaginationMeta,
};

// Enhanced types for better UX
export type UserWithDisplayName = User & {
  displayName: string;
};

export type UserFilters = {
  search?: string;
  role?: UserRole;
  status?: UserStatus;
  page?: number;
  limit?: number;
};

export type UserSortOptions = {
  sortBy: 'email' | 'firstName' | 'lastName' | 'createdAt';
  sortOrder: 'asc' | 'desc';
};
```

### Service Type Patterns

#### Typed Service Methods
```typescript
// services/AdminService.ts - Type-safe service methods
export class AdminService extends BaseService {
  /**
   * Type-safe notification method
   * Returns exactly what the generated SDK specifies
   */
  static async sendSystemNotification(
    message: string,
    title?: string,
    priority: BroadcastPriority = 'normal'
  ): Promise<BroadcastResultResponse> {
    const response = await this.client.api.broadcastMessageApiV1AdminBroadcastPost({
      body: {
        message,
        title,
        priority,
        target: 'all_users' as BroadcastTarget,
        persistent: true,
      } satisfies BroadcastMessageRequest
    });

    if (!response.data) {
      throw new Error('Failed to send notification');
    }

    return response.data; // TypeScript knows this is BroadcastResultResponse
  }

  /**
   * Type-safe maintenance mode with full type inference
   */
  static async enableMaintenanceMode(
    reason: string,
    estimatedDurationMinutes?: number
  ): Promise<MaintenanceStatusResponse> {
    const request: MaintenanceModeRequest = {
      enable: true,
      reason,
      estimated_duration_minutes: estimatedDurationMinutes,
      grace_period_minutes: 5,
      notify_users: true,
    };

    const response = await this.client.api.manageMaintenanceModeApiV1AdminMaintenancePost({
      body: request
    });

    if (!response.data) {
      throw new Error('Failed to enable maintenance mode');
    }

    return response.data; // TypeScript infers MaintenanceStatusResponse
  }
}
```

---

## 🔄 Business Logic Layer

### Service Method Patterns

#### Three Levels of Abstraction
```typescript
export class UserService extends BaseService {
  // Level 1: Raw SDK wrapper - direct mapping
  static async getUser(userId: string) {
    const response = await this.client.api.getUserApiV1UsersUserIdGet({
      path: { user_id: userId }
    });
    if (!response.data) {
      throw new Error('Failed to get user');
    }
    return response.data;
  }

  // Level 2: Business logic - validation and defaults
  static async createUserWithValidation(userData: CreateUserRequest) {
    // Business validation
    if (!userData.email.includes('@')) {
      throw new Error('Invalid email format');
    }

    if (userData.password.length < 8) {
      throw new Error('Password must be at least 8 characters');
    }

    // Add business defaults
    const requestWithDefaults: CreateUserRequest = {
      ...userData,
      role: userData.role || 'user' as UserRole,
    };

    return this.createUser(requestWithDefaults);
  }

  // Level 3: High-level operations - complex workflows
  static async createAdminUser(email: string, firstName: string, lastName: string) {
    // Generate secure password
    const password = this.generateSecurePassword();

    // Create user with admin role
    const user = await this.createUserWithValidation({
      email,
      firstName,
      lastName,
      password,
      role: 'admin' as UserRole,
    });

    // Send welcome email (another service)
    await this.sendWelcomeEmail(user.email, password);

    // Log admin creation
    console.log(`Admin user created: ${user.email}`);

    return user;
  }

  // Utility methods
  private static generateSecurePassword(): string {
    return Math.random().toString(36).slice(-12) + Math.random().toString(36).slice(-12);
  }

  private static async sendWelcomeEmail(email: string, password: string) {
    // Implementation would use EmailService or similar
    await AdminService.sendAdminAlert(
      `New admin user created: ${email}`,
      'normal'
    );
  }
}
```

### Bulk Operations Pattern
```typescript
export class UserService extends BaseService {
  /**
   * Bulk operations with error handling and progress tracking
   */
  static async bulkCreateUsers(
    users: CreateUserRequest[],
    onProgress?: (completed: number, total: number) => void
  ) {
    const results = {
      successful: [] as User[],
      failed: [] as { user: CreateUserRequest; error: string }[],
    };

    for (let i = 0; i < users.length; i++) {
      try {
        const user = await this.createUserWithValidation(users[i]);
        results.successful.push(user);
      } catch (error) {
        results.failed.push({
          user: users[i],
          error: error instanceof Error ? error.message : 'Unknown error',
        });
      }

      // Report progress
      onProgress?.(i + 1, users.length);
    }

    return results;
  }

  /**
   * Batch operations with concurrency control
   */
  static async bulkUpdateUsers(
    updates: Array<{ id: string; updates: UpdateUserRequest }>,
    concurrency = 3
  ) {
    const chunks = this.chunkArray(updates, concurrency);
    const results = [];

    for (const chunk of chunks) {
      const chunkPromises = chunk.map(({ id, updates }) =>
        this.updateUser(id, updates).catch(error => ({ error, id }))
      );

      const chunkResults = await Promise.all(chunkPromises);
      results.push(...chunkResults);
    }

    return results;
  }

  private static chunkArray<T>(array: T[], size: number): T[][] {
    const chunks = [];
    for (let i = 0; i < array.length; i += size) {
      chunks.push(array.slice(i, i + size));
    }
    return chunks;
  }
}
```

---

## ⚛️ Integration with React

### Service Usage in Components

#### Simple Component with Service
```typescript
// components/AdminPanel.tsx
import { useState } from 'react';
import { AdminService } from '@/apiServer/services';
import { Button } from '@/components/ui/Button';
import { toast } from 'react-hot-toast';

export function AdminPanel() {
  const [loading, setLoading] = useState(false);

  const handleSystemAlert = async () => {
    setLoading(true);
    try {
      // Clean, simple service call
      await AdminService.sendSystemNotification(
        'System maintenance scheduled for tonight',
        'Maintenance Notice',
        'high'
      );
      toast.success('Alert sent to all users');
    } catch (error) {
      toast.error('Failed to send alert');
    } finally {
      setLoading(false);
    }
  };

  const handleMaintenanceMode = async () => {
    setLoading(true);
    try {
      await AdminService.enableMaintenanceMode(
        'Scheduled maintenance',
        60 // 1 hour
      );
      toast.success('Maintenance mode enabled');
    } catch (error) {
      toast.error('Failed to enable maintenance mode');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <Button
        onClick={handleSystemAlert}
        loading={loading}
        variant="outline"
      >
        Send System Alert
      </Button>

      <Button
        onClick={handleMaintenanceMode}
        loading={loading}
        variant="destructive"
      >
        Enable Maintenance Mode
      </Button>
    </div>
  );
}
```

#### With SWR for Data Fetching
```typescript
// components/UserManagement.tsx
import { useState } from 'react';
import useSWR from 'swr';
import { UserService } from '@/apiServer/services';
import type { UserFilters } from '@/apiServer/services/types/user';

export function UserManagement() {
  const [filters, setFilters] = useState<UserFilters>({
    page: 1,
    limit: 20,
  });

  // Clean SWR integration with service
  const { data: users, error, mutate } = useSWR(
    ['users', filters],
    ([_, filters]) => UserService.getUsers(filters)
  );

  const handleCreateUser = async (userData: CreateUserRequest) => {
    try {
      await UserService.createUserWithValidation(userData);

      // Refresh data after creation
      mutate();

      toast.success('User created successfully');
    } catch (error) {
      toast.error('Failed to create user');
    }
  };

  if (error) return <div>Error loading users</div>;
  if (!users) return <div>Loading...</div>;

  return (
    <div>
      <UserList users={users.users} />
      <UserForm onSubmit={handleCreateUser} />
    </div>
  );
}
```

#### Custom Hook for Service
```typescript
// hooks/useAdminOperations.ts
import { useState, useCallback } from 'react';
import { AdminService } from '@/apiServer/services';
import { toast } from 'react-hot-toast';

export function useAdminOperations() {
  const [loading, setLoading] = useState(false);

  const sendNotification = useCallback(async (
    message: string,
    title?: string,
    priority: 'low' | 'normal' | 'high' | 'urgent' | 'critical' = 'normal'
  ) => {
    setLoading(true);
    try {
      const result = await AdminService.sendSystemNotification(message, title, priority);
      toast.success(`Notification sent to ${result.delivered_count} users`);
      return result;
    } catch (error) {
      toast.error('Failed to send notification');
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const toggleMaintenanceMode = useCallback(async (enable: boolean, reason?: string) => {
    setLoading(true);
    try {
      if (enable) {
        await AdminService.enableMaintenanceMode(reason || 'Maintenance', 30);
        toast.success('Maintenance mode enabled');
      } else {
        await AdminService.disableMaintenanceMode();
        toast.success('Maintenance mode disabled');
      }
    } catch (error) {
      toast.error('Failed to toggle maintenance mode');
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    sendNotification,
    toggleMaintenanceMode,
  };
}

// Usage in component
function AdminControls() {
  const { loading, sendNotification, toggleMaintenanceMode } = useAdminOperations();

  return (
    <div>
      <Button
        onClick={() => sendNotification('System update complete', 'Update Notice', 'normal')}
        loading={loading}
      >
        Send Update Notice
      </Button>

      <Button
        onClick={() => toggleMaintenanceMode(true, 'Emergency maintenance')}
        loading={loading}
        variant="destructive"
      >
        Emergency Maintenance
      </Button>
    </div>
  );
}
```

---

## 🎯 Key Benefits Summary

### ✅ Why This Architecture Works

#### 1. **Automatic Type Safety**
- **Generated SDK** provides 100% accurate types from backend
- **Service Layer** adds business logic while preserving types
- **No manual type definitions** needed for API data
- **Type errors caught at compile time** instead of runtime

#### 2. **Clean Component Code**
```typescript
// ❌ Without service layer - ugly and verbose
const response = await api.api.broadcastMessageApiV1AdminBroadcastPost({
  body: {
    message: "System maintenance",
    title: "Notice",
    priority: "high",
    target: "all_users",
    persistent: true
  }
});

// ✅ With service layer - clean and readable
await AdminService.sendSystemNotification(
  "System maintenance",
  "Notice",
  "high"
);
```

#### 3. **Centralized Business Logic**
- **Common operations** simplified into single methods
- **Validation and defaults** handled in service layer
- **Error handling** consistent across the application
- **Complex workflows** encapsulated and reusable

#### 4. **Easy Maintenance**
- **API changes** reflected in generated SDK automatically
- **Service methods** adapt to SDK changes with minimal effort
- **Component code** remains stable when API evolves
- **Type safety** ensures compatibility during updates

#### 5. **Developer Experience**
- **Auto-completion** works perfectly with generated types
- **Clear method names** instead of generated endpoint names
- **Consistent patterns** across all services
- **Easy testing** with mockable service methods

---

## 🚀 Implementation Checklist

### Setup Phase
- [ ] **OpenAPI schema** available from backend
- [ ] **SDK generation** configured and working
- [ ] **Base client** initialized in `client.ts`
- [ ] **BaseService** implemented with error handling

### Service Layer Phase
- [ ] **BaseService** extends with common patterns
- [ ] **Domain services** created (Admin, User, etc.)
- [ ] **Type proxies** set up for clean imports
- [ ] **Business methods** implemented with sensible defaults

### Integration Phase
- [ ] **React components** use services instead of direct SDK
- [ ] **SWR/React Query** configured with service methods
- [ ] **Custom hooks** created for complex operations
- [ ] **Error handling** consistent across components

### Quality Phase
- [ ] **Type checking** passes with zero `any` types
- [ ] **Service methods** have clear, human-readable names
- [ ] **Business logic** centralized in service layer
- [ ] **Components** are simple and focused on UI

---

## 🏷️ Metadata
**Architecture**: Auto-generated SDK + Service Layer
**Type Safety**: 100% with generated TypeScript types
**Pattern**: Business logic over generated clients
**Benefits**: Clean components, centralized logic, automatic types
**Maintenance**: SDK auto-updates, service layer provides stability

%%AI_HINT: This architecture combines the benefits of auto-generated type-safe clients with the convenience of hand-crafted business logic layer%%
