# 📝 Next.js Style Guide %%PRIORITY:MEDIUM%%

## 🎯 Quick Summary
Code formatting, naming conventions, and project structure guidelines for Next.js applications to ensure consistency, readability, and maintainability across teams.

## 📋 Table of Contents
1. [Project Structure](#project-structure)
2. [Naming Conventions](#naming-conventions)
3. [Import Organization](#import-organization)
4. [Component Structure](#component-structure)
5. [CSS and Styling](#css-and-styling)
6. [TypeScript Conventions](#typescript-conventions)

## 🔑 Key Principles at a Glance
- **Consistency**: Uniform naming and structure across the project
- **Clarity**: Self-documenting code with meaningful names
- **Organization**: Logical file and folder structure
- **Standards**: Follow established conventions and best practices
- **Tooling**: Automated formatting and linting
- **Scalability**: Structure that grows with the project

---

## 📁 Project Structure

### App Router Structure (Next.js 13+)
```
project-root/
├── app/                          # App Router directory
│   ├── (auth)/                   # Route groups
│   │   ├── login/
│   │   └── register/
│   ├── dashboard/
│   │   ├── users/
│   │   ├── products/
│   │   └── layout.tsx
│   ├── api/                      # API routes
│   │   ├── users/
│   │   └── products/
│   ├── globals.css               # Global styles
│   ├── layout.tsx                # Root layout
│   ├── loading.tsx               # Global loading UI
│   ├── error.tsx                 # Global error UI
│   ├── not-found.tsx             # 404 page
│   └── page.tsx                  # Home page
├── components/                   # Reusable components
│   ├── ui/                       # Basic UI components
│   │   ├── Button/
│   │   │   ├── index.ts          # Export barrel
│   │   │   ├── Button.tsx        # Component
│   │   │   ├── Button.types.ts   # Types
│   │   │   ├── Button.test.tsx   # Tests
│   │   │   └── Button.stories.tsx # Storybook
│   │   ├── Input/
│   │   └── Modal/
│   ├── features/                 # Feature-specific components
│   │   ├── UserManagement/
│   │   │   ├── components/       # Feature components
│   │   │   ├── hooks/           # Feature hooks
│   │   │   ├── context/         # Feature context
│   │   │   ├── types/           # Feature types
│   │   │   └── index.ts         # Feature exports
│   │   └── ProductCatalog/
│   └── layout/                   # Layout components
│       ├── Header/
│       ├── Sidebar/
│       └── Footer/
├── lib/                          # Utility libraries
│   ├── utils.ts                  # General utilities
│   ├── validations.ts            # Zod schemas
│   ├── constants.ts              # App constants
│   └── auth.ts                   # Auth configuration
├── hooks/                        # Global custom hooks
│   ├── useLocalStorage.ts
│   ├── useDebounce.ts
│   └── useApi.ts
├── services/                     # API services
│   ├── base/
│   │   ├── BaseService.ts
│   │   └── ApiError.ts
│   ├── user/
│   │   ├── UserService.ts
│   │   └── types.ts
│   └── product/
├── types/                        # Global type definitions
│   ├── api.ts                    # API types
│   ├── global.ts                 # Global types
│   └── env.ts                    # Environment types
├── styles/                       # Styling files
│   ├── globals.css               # Global styles
│   ├── components.css            # Component styles
│   └── utilities.css             # Utility classes
├── public/                       # Static assets
│   ├── images/
│   ├── icons/
│   └── favicon.ico
├── docs/                         # Documentation
│   ├── README.md
│   ├── API.md
│   └── DEPLOYMENT.md
├── __tests__/                    # Global tests
│   ├── setup.ts
│   ├── utils.ts
│   └── __mocks__/
├── .env.local                    # Environment variables
├── .env.example                  # Example environment
├── .gitignore                    # Git ignore rules
├── .eslintrc.json               # ESLint configuration
├── .prettierrc                   # Prettier configuration
├── tailwind.config.js            # Tailwind CSS config
├── tsconfig.json                 # TypeScript config
├── next.config.js                # Next.js config
├── package.json                  # Dependencies
└── README.md                     # Project documentation
```

### Pages Router Structure (Legacy)
```
project-root/
├── pages/                        # Page components
│   ├── api/                      # API routes
│   ├── auth/
│   │   ├── login.tsx
│   │   └── register.tsx
│   ├── dashboard/
│   │   ├── index.tsx
│   │   ├── users.tsx
│   │   └── products.tsx
│   ├── _app.tsx                  # App component
│   ├── _document.tsx             # Document component
│   ├── 404.tsx                   # Custom 404
│   ├── 500.tsx                   # Custom 500
│   └── index.tsx                 # Home page
├── components/                   # Same structure as App Router
├── lib/                          # Same structure as App Router
├── styles/                       # Same structure as App Router
├── public/                       # Same structure as App Router
└── [other files same as above]
```

---

## 🏷️ Naming Conventions

### File and Directory Naming

#### Component Files
```
// ✅ GOOD - PascalCase for components
components/
├── UserProfile.tsx               # Single component
├── UserManagement/               # Feature directory
│   ├── index.ts                  # Export barrel
│   ├── UserList.tsx              # Component
│   ├── UserList.types.ts         # Types
│   ├── UserList.test.tsx         # Tests
│   └── UserList.stories.tsx      # Stories

// ❌ BAD - Inconsistent naming
components/
├── userProfile.tsx               # camelCase (wrong)
├── user-profile.tsx              # kebab-case (wrong)
├── user_profile.tsx              # snake_case (wrong)
```

#### Non-Component Files
```
// ✅ GOOD - camelCase for utilities, services, hooks
lib/
├── utils.ts                      # Utilities
├── apiClient.ts                  # Services
├── constants.ts                  # Constants

hooks/
├── useLocalStorage.ts            # Custom hooks
├── useDebounce.ts
├── useUserManagement.ts

services/
├── userService.ts                # Service files
├── productService.ts
├── authService.ts

// ✅ GOOD - kebab-case for config files
├── .eslintrc.json
├── .prettierrc
├── next.config.js
├── tailwind.config.js
```

#### Directory Structure Rules
```
// ✅ GOOD - Clear hierarchy and grouping
features/
├── UserManagement/               # PascalCase feature
│   ├── components/               # lowercase grouped items
│   │   ├── UserList/             # PascalCase components
│   │   └── UserForm/
│   ├── hooks/                    # lowercase grouped items
│   │   ├── useUsers.ts           # camelCase hooks
│   │   └── useUserForm.ts
│   └── services/                 # lowercase grouped items
│       └── userService.ts        # camelCase services

// ❌ BAD - Mixed conventions
features/
├── user_management/              # snake_case (wrong)
├── User-Management/              # kebab-case with caps (wrong)
├── userManagement/               # camelCase (wrong for directory)
```

### Variable and Function Naming

#### TypeScript Naming Conventions
```typescript
// ✅ GOOD - Clear, descriptive names
interface User {
  id: string;
  firstName: string;
  lastName: string;
  emailAddress: string;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

// Component props interface
interface UserProfileProps {
  user: User;
  isEditable: boolean;
  onSave: (user: User) => void;
  onCancel: () => void;
}

// Service methods
class UserService {
  static async getUserById(userId: string): Promise<User> { }
  static async updateUserProfile(userId: string, updates: Partial<User>): Promise<User> { }
  static async deleteUser(userId: string): Promise<void> { }
}

// Hook naming
function useUserManagement() {
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createUser = useCallback(async (userData: CreateUserRequest) => {
    // Implementation
  }, []);

  return {
    selectedUser,
    isLoading,
    error,
    createUser,
    updateUser,
    deleteUser,
  };
}

// ❌ BAD - Unclear, abbreviated names
interface U {
  id: string;
  fn: string;          // firstName (unclear)
  ln: string;          // lastName (unclear)
  em: string;          // email (unclear)
  act: boolean;        // isActive (unclear)
}

function useUM() { }   // useUserManagement (unclear)
const usr = data.user; // user (abbreviated)
const handleClk = () => { }; // handleClick (abbreviated)
```

#### Constants and Enums
```typescript
// ✅ GOOD - SCREAMING_SNAKE_CASE for constants
export const API_BASE_URL = 'https://api.example.com';
export const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
export const DEFAULT_PAGE_SIZE = 20;
export const CACHE_KEYS = {
  USER_LIST: 'user-list',
  USER_PROFILE: 'user-profile',
  PRODUCT_CATALOG: 'product-catalog',
} as const;

// ✅ GOOD - PascalCase for enums
export enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  USER = 'user',
  GUEST = 'guest',
}

export enum OrderStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  SHIPPED = 'shipped',
  DELIVERED = 'delivered',
  CANCELLED = 'cancelled',
}

// ❌ BAD - Mixed conventions
const apiUrl = 'https://api.example.com';        // camelCase (wrong for constant)
const max_file_size = 5000000;                   // snake_case (wrong)
enum userRole { admin, manager }                 // camelCase enum (wrong)
```

---

## 📦 Import Organization

### Import Order and Grouping
```typescript
// ✅ GOOD - Organized import structure
// 1. React and Next.js imports
import React, { useState, useCallback, useMemo } from 'react';
import { NextPage } from 'next';
import { useRouter } from 'next/router';
import Image from 'next/image';
import Head from 'next/head';

// 2. Third-party library imports
import { z } from 'zod';
import { format } from 'date-fns';
import { toast } from 'react-hot-toast';

// 3. Internal imports (alphabetical by path)
import { Button, Input, Modal } from '@/components/ui';
import { UserList, UserForm } from '@/components/features/UserManagement';
import { useAuth } from '@/hooks/useAuth';
import { useUsers } from '@/hooks/useUsers';
import { UserService } from '@/services/userService';
import { User, CreateUserRequest } from '@/types/user';
import { cn } from '@/lib/utils';

// 4. Type-only imports (at the end)
import type { GetServerSideProps } from 'next';
import type { UserListResponse } from '@/types/api';

// ❌ BAD - Mixed and unorganized imports
import { cn } from '@/lib/utils';
import React from 'react';
import { UserService } from '@/services/userService';
import { format } from 'date-fns';
import { Button } from '@/components/ui';
import { NextPage } from 'next';
```

### Export Patterns
```typescript
// ✅ GOOD - Named exports for components
// components/ui/Button/Button.tsx
export function Button({ children, ...props }: ButtonProps) {
  return <button {...props}>{children}</button>;
}

// components/ui/Button/index.ts - Export barrel
export { Button } from './Button';
export type { ButtonProps } from './Button.types';

// ✅ GOOD - Default exports for pages
// pages/dashboard.tsx or app/dashboard/page.tsx
export default function DashboardPage() {
  return <div>Dashboard</div>;
}

// ✅ GOOD - Named exports for utilities
// lib/utils.ts
export function formatCurrency(amount: number): string { }
export function validateEmail(email: string): boolean { }
export function debounce<T extends (...args: any[]) => any>(fn: T, delay: number): T { }

// ✅ GOOD - Mixed exports when appropriate
// hooks/useUsers.ts
export function useUsers() { }
export function useUser(id: string) { }
export default useUsers; // Primary hook as default

// ❌ BAD - Default exports for components
export default function Button() { } // Should be named export

// ❌ BAD - Default exports for utilities
export default function formatCurrency() { } // Should be named export
```

---

## 🧩 Component Structure

### Component File Organization
```typescript
// ✅ GOOD - Organized component structure
// components/features/UserManagement/UserList.tsx

// 1. Imports (organized as shown above)
import React, { useState, useCallback, useMemo } from 'react';
import { Button, Table, Badge } from '@/components/ui';
import { useUsers } from '@/hooks/useUsers';
import { User } from '@/types/user';

// 2. Types and interfaces
interface UserListProps {
  filters?: UserFilters;
  onUserSelect?: (user: User) => void;
  selectable?: boolean;
  className?: string;
}

interface PreparedUserData {
  id: string;
  displayName: string;
  roleDisplay: string;
  statusBadge: BadgeProps;
}

// 3. Helper functions (outside component)
function formatUserRole(role: UserRole): string {
  const roleLabels = {
    [UserRole.ADMIN]: 'Administrator',
    [UserRole.MANAGER]: 'Manager',
    [UserRole.USER]: 'User',
  };
  return roleLabels[role];
}

function getUserStatusBadge(status: UserStatus): BadgeProps {
  const statusConfig = {
    [UserStatus.ACTIVE]: { variant: 'success', text: 'Active' },
    [UserStatus.INACTIVE]: { variant: 'warning', text: 'Inactive' },
  };
  return statusConfig[status];
}

// 4. Main component
export function UserList({
  filters,
  onUserSelect,
  selectable = false,
  className,
}: UserListProps) {
  // 4a. Hooks (state, effects, custom hooks)
  const { users, isLoading, error } = useUsers(filters);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // 4b. Memoized values
  const preparedUsers = useMemo((): PreparedUserData[] => {
    if (!users?.users) return [];

    return users.users.map(user => ({
      id: user.id,
      displayName: `${user.firstName} ${user.lastName}`,
      roleDisplay: formatUserRole(user.role),
      statusBadge: getUserStatusBadge(user.status),
    }));
  }, [users?.users]);

  // 4c. Event handlers
  const handleUserClick = useCallback((user: PreparedUserData) => {
    setSelectedId(user.id);
    if (onUserSelect) {
      const originalUser = users?.users.find(u => u.id === user.id);
      if (originalUser) {
        onUserSelect(originalUser);
      }
    }
  }, [users?.users, onUserSelect]);

  // 4d. Early returns
  if (isLoading) {
    return <UserListSkeleton className={className} />;
  }

  if (error) {
    return <ErrorMessage message={error} className={className} />;
  }

  if (preparedUsers.length === 0) {
    return <EmptyState message="No users found" className={className} />;
  }

  // 4e. Main render
  return (
    <div className={cn('space-y-4', className)}>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Role</TableHead>
            <TableHead>Status</TableHead>
            {selectable && <TableHead>Select</TableHead>}
          </TableRow>
        </TableHeader>
        <TableBody>
          {preparedUsers.map(user => (
            <TableRow
              key={user.id}
              className={cn(
                'cursor-pointer hover:bg-muted/50',
                selectedId === user.id && 'bg-muted'
              )}
              onClick={() => handleUserClick(user)}
            >
              <TableCell>{user.displayName}</TableCell>
              <TableCell>{user.roleDisplay}</TableCell>
              <TableCell>
                <Badge {...user.statusBadge} />
              </TableCell>
              {selectable && (
                <TableCell>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleUserClick(user);
                    }}
                  >
                    Select
                  </Button>
                </TableCell>
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

// 5. Component displayName (for debugging)
UserList.displayName = 'UserList';
```

### Hook Organization
```typescript
// ✅ GOOD - Well-organized custom hook
// hooks/useUserManagement.ts

import { useState, useCallback, useMemo } from 'react';
import { UserService } from '@/services/userService';
import { User, CreateUserRequest, UpdateUserRequest } from '@/types/user';

interface UseUserManagementOptions {
  initialFilters?: UserFilters;
  autoLoad?: boolean;
}

interface UseUserManagementReturn {
  // State
  users: User[];
  selectedUser: User | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  loadUsers: () => Promise<void>;
  selectUser: (user: User | null) => void;
  createUser: (userData: CreateUserRequest) => Promise<User>;
  updateUser: (userId: string, updates: UpdateUserRequest) => Promise<User>;
  deleteUser: (userId: string) => Promise<void>;

  // Computed
  selectedUserCount: number;
  hasError: boolean;
  isEmpty: boolean;
}

export function useUserManagement(
  options: UseUserManagementOptions = {}
): UseUserManagementReturn {
  const { initialFilters = {}, autoLoad = true } = options;

  // State
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(autoLoad);
  const [error, setError] = useState<string | null>(null);

  // Load users effect
  useEffect(() => {
    if (autoLoad) {
      loadUsers();
    }
  }, [autoLoad]);

  // Actions
  const loadUsers = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await UserService.getUsers(initialFilters);
      setUsers(response.users);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setIsLoading(false);
    }
  }, [initialFilters]);

  const selectUser = useCallback((user: User | null) => {
    setSelectedUser(user);
  }, []);

  const createUser = useCallback(async (userData: CreateUserRequest): Promise<User> => {
    setIsLoading(true);
    setError(null);

    try {
      const newUser = await UserService.createUser(userData);
      setUsers(prev => [...prev, newUser]);
      return newUser;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create user';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // ... other actions

  // Computed values
  const computedValues = useMemo(() => ({
    selectedUserCount: users.length,
    hasError: error !== null,
    isEmpty: users.length === 0,
  }), [users.length, error]);

  return {
    // State
    users,
    selectedUser,
    isLoading,
    error,

    // Actions
    loadUsers,
    selectUser,
    createUser,
    updateUser,
    deleteUser,

    // Computed
    ...computedValues,
  };
}
```

---

## 🎨 CSS and Styling

### Tailwind CSS Conventions

#### Class Organization
```tsx
// ✅ GOOD - Organized Tailwind classes
function UserCard({ user, isSelected }: UserCardProps) {
  return (
    <div className={cn(
      // Layout
      'flex items-center justify-between p-4',
      // Spacing
      'space-x-4',
      // Background and borders
      'bg-white border border-gray-200 rounded-lg',
      // Shadows and effects
      'shadow-sm hover:shadow-md',
      // Transitions
      'transition-all duration-200',
      // Conditional styles
      isSelected && 'ring-2 ring-blue-500 border-blue-300',
      'hover:bg-gray-50'
    )}>
      {/* Content */}
    </div>
  );
}

// ❌ BAD - Unorganized classes
function UserCard({ user, isSelected }: UserCardProps) {
  return (
    <div className="p-4 bg-white hover:bg-gray-50 flex border transition-all rounded-lg shadow-sm items-center space-x-4 justify-between border-gray-200 duration-200 hover:shadow-md">
      {/* Hard to read and maintain */}
    </div>
  );
}
```

#### Responsive Design Patterns
```tsx
// ✅ GOOD - Mobile-first responsive design
function ProductGrid({ products }: ProductGridProps) {
  return (
    <div className={cn(
      // Mobile: single column
      'grid grid-cols-1 gap-4',
      // Tablet: 2 columns
      'sm:grid-cols-2 sm:gap-6',
      // Desktop: 3 columns
      'lg:grid-cols-3 lg:gap-8',
      // Large desktop: 4 columns
      'xl:grid-cols-4'
    )}>
      {products.map(product => (
        <ProductCard
          key={product.id}
          product={product}
          className={cn(
            // Mobile styles
            'w-full',
            // Desktop styles
            'lg:max-w-sm'
          )}
        />
      ))}
    </div>
  );
}
```

#### Custom CSS Organization
```css
/* styles/globals.css */

/* 1. Base styles */
@tailwind base;
@tailwind components;
@tailwind utilities;

/* 2. Custom base styles */
@layer base {
  html {
    scroll-behavior: smooth;
  }

  body {
    @apply bg-background text-foreground;
    font-feature-settings: "rlig" 1, "calt" 1;
  }
}

/* 3. Component styles */
@layer components {
  .btn {
    @apply inline-flex items-center justify-center rounded-md text-sm font-medium;
    @apply ring-offset-background transition-colors;
    @apply focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2;
    @apply disabled:pointer-events-none disabled:opacity-50;
  }

  .btn-primary {
    @apply bg-primary text-primary-foreground hover:bg-primary/90;
  }

  .btn-secondary {
    @apply bg-secondary text-secondary-foreground hover:bg-secondary/80;
  }
}

/* 4. Utility styles */
@layer utilities {
  .scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
  .scrollbar-hide::-webkit-scrollbar {
    display: none;
  }

  .text-balance {
    text-wrap: balance;
  }
}
```

---

## 📘 TypeScript Conventions

### Type Definitions
```typescript
// ✅ GOOD - Well-structured type definitions
// types/user.ts

// Base interfaces
export interface BaseEntity {
  id: string;
  createdAt: string;
  updatedAt: string;
}

export interface User extends BaseEntity {
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  status: UserStatus;
  avatar?: string;
  lastLoginAt?: string;
}

// Enums with clear values
export enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  USER = 'user',
  GUEST = 'guest',
}

export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
  PENDING = 'pending',
}

// Request/Response types
export interface CreateUserRequest {
  email: string;
  firstName: string;
  lastName: string;
  password: string;
  role?: UserRole;
}

export interface UpdateUserRequest {
  firstName?: string;
  lastName?: string;
  role?: UserRole;
  status?: UserStatus;
  avatar?: string;
}

export interface UserListResponse {
  users: User[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

// Utility types
export type UserWithoutSensitiveData = Omit<User, 'password'>;
export type PartialUser = Partial<User>;
export type UserKeys = keyof User;
export type UserRoleKeys = keyof typeof UserRole;

// Generic types
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: PaginationMeta;
}

// Component prop types
export interface UserComponentProps {
  user: User;
  className?: string;
  onEdit?: (user: User) => void;
  onDelete?: (userId: string) => void;
}

// Event handler types
export type UserEventHandler = (user: User) => void;
export type UserIdEventHandler = (userId: string) => void;
export type AsyncUserEventHandler = (user: User) => Promise<void>;
```

### Generic Type Patterns
```typescript
// ✅ GOOD - Reusable generic patterns
// types/api.ts

export interface RequestConfig {
  timeout?: number;
  retries?: number;
  cache?: boolean;
}

export interface BaseService<T, CreateRequest, UpdateRequest> {
  getAll(params?: Record<string, unknown>): Promise<T[]>;
  getById(id: string): Promise<T>;
  create(data: CreateRequest): Promise<T>;
  update(id: string, data: UpdateRequest): Promise<T>;
  delete(id: string): Promise<void>;
}

// Service implementations
export interface UserService extends BaseService<User, CreateUserRequest, UpdateUserRequest> {
  getUsersByRole(role: UserRole): Promise<User[]>;
  activateUser(userId: string): Promise<User>;
  deactivateUser(userId: string): Promise<User>;
}

// Hook return types
export interface UseEntityReturn<T> {
  data: T[];
  item: T | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  create: (data: unknown) => Promise<T>;
  update: (id: string, data: unknown) => Promise<T>;
  remove: (id: string) => Promise<void>;
}

// Form types
export interface FormState<T> {
  values: T;
  errors: Partial<Record<keyof T, string>>;
  touched: Partial<Record<keyof T, boolean>>;
  isValid: boolean;
  isSubmitting: boolean;
}

export interface FormActions<T> {
  setFieldValue: <K extends keyof T>(field: K, value: T[K]) => void;
  setFieldError: <K extends keyof T>(field: K, error: string) => void;
  setFieldTouched: <K extends keyof T>(field: K, touched: boolean) => void;
  reset: () => void;
  submit: () => Promise<void>;
}
```

---

## 🛠️ Development Tools Configuration

### ESLint Configuration
```json
// .eslintrc.json
{
  "extends": [
    "next/core-web-vitals",
    "@typescript-eslint/recommended",
    "prettier"
  ],
  "parser": "@typescript-eslint/parser",
  "plugins": ["@typescript-eslint", "unused-imports"],
  "rules": {
    // TypeScript specific
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/prefer-const": "error",
    "@typescript-eslint/no-non-null-assertion": "warn",

    // Import organization
    "unused-imports/no-unused-imports": "error",
    "import/order": [
      "error",
      {
        "groups": [
          "builtin",
          "external",
          "internal",
          "parent",
          "sibling",
          "index"
        ],
        "newlines-between": "always",
        "alphabetize": {
          "order": "asc",
          "caseInsensitive": true
        }
      }
    ],

    // React specific
    "react/jsx-key": "error",
    "react/jsx-no-duplicate-props": "error",
    "react/jsx-uses-react": "off",
    "react/react-in-jsx-scope": "off",

    // General
    "prefer-const": "error",
    "no-var": "error",
    "no-console": "warn",
    "no-debugger": "error"
  },
  "settings": {
    "import/resolver": {
      "typescript": {
        "project": "./tsconfig.json"
      }
    }
  }
}
```

### Prettier Configuration
```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false,
  "bracketSpacing": true,
  "arrowParens": "avoid",
  "endOfLine": "lf",
  "bracketSameLine": false,
  "plugins": ["prettier-plugin-tailwindcss"]
}
```

### TypeScript Configuration
```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "ES2022"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@/components/*": ["./src/components/*"],
      "@/lib/*": ["./src/lib/*"],
      "@/hooks/*": ["./src/hooks/*"],
      "@/services/*": ["./src/services/*"],
      "@/types/*": ["./src/types/*"]
    }
  },
  "include": [
    "next-env.d.ts",
    "**/*.ts",
    "**/*.tsx",
    ".next/types/**/*.ts"
  ],
  "exclude": [
    "node_modules"
  ]
}
```

---

## 🏷️ Metadata
**Framework**: Next.js 13+ with TypeScript
**Styling**: Tailwind CSS with CSS-in-JS support
**Tooling**: ESLint, Prettier, TypeScript strict mode
**Organization**: Feature-based structure with clear conventions
**Standards**: Consistent naming, imports, and component patterns

%%AI_HINT: These style guidelines ensure consistent, maintainable, and scalable Next.js codebases that work well with AI assistance and team collaboration%%
