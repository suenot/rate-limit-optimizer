# 🧩 Next.js Component Patterns %%PRIORITY:HIGH%%

## 🎯 Quick Summary
Standardized React component patterns for Next.js applications, including component architecture, state management, context usage, and performance optimization techniques.

## 📋 Table of Contents
1. [Component Architecture](#component-architecture)
2. [Data Preparation Pattern](#data-preparation-pattern)
3. [Context Over Props](#context-over-props)
4. [State Management](#state-management)
5. [Performance Optimization](#performance-optimization)
6. [Component Testing](#component-testing)

## 🔑 Key Principles at a Glance
- **Data Preparation**: Transform data in useMemo, never in JSX
- **Context Over Props**: Use React Context instead of prop drilling
- **Single Responsibility**: One concern per component
- **Type Safety**: Full TypeScript coverage for all props and state
- **Performance**: Proper memoization and optimization
- **Testability**: Components designed for easy testing

---

## 🏗️ Component Architecture

### File Organization Patterns

#### Feature-Based Structure
```
components/
├── ui/                          # Reusable UI components
│   ├── Button/
│   │   ├── index.ts            # Export barrel
│   │   ├── Button.tsx          # Main component
│   │   ├── Button.types.ts     # TypeScript interfaces
│   │   ├── Button.test.tsx     # Tests
│   │   └── Button.stories.tsx  # Storybook stories
│   ├── Input/
│   ├── Modal/
│   └── ...
├── features/                    # Feature-specific components
│   ├── UserManagement/
│   │   ├── components/
│   │   │   ├── UserList/
│   │   │   ├── UserForm/
│   │   │   └── UserProfile/
│   │   ├── hooks/
│   │   │   ├── useUsers.ts
│   │   │   └── useUserForm.ts
│   │   ├── context/
│   │   │   └── UserContext.tsx
│   │   └── index.ts
│   ├── ProductCatalog/
│   └── OrderManagement/
└── layout/                      # Layout components
    ├── Header/
    ├── Sidebar/
    ├── Footer/
    └── Layout/
```

#### Component Types Hierarchy
```typescript
// Component classification by responsibility
export enum ComponentType {
  // Pure UI components (no business logic)
  UI = 'ui',

  // Business logic components (connected to data)
  FEATURE = 'feature',

  // Layout and structure components
  LAYOUT = 'layout',

  // Page-level components
  PAGE = 'page',
}

// Base component props interface
export interface BaseComponentProps {
  className?: string;
  children?: ReactNode;
  testId?: string;
}

// Feature component props (includes data and actions)
export interface FeatureComponentProps extends BaseComponentProps {
  loading?: boolean;
  error?: string | null;
}

// UI component props (presentation only)
export interface UIComponentProps extends BaseComponentProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
}
```

### Component Definition Patterns

#### UI Component Pattern
```typescript
// components/ui/Button/Button.types.ts
export interface ButtonProps extends UIComponentProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  onClick?: (event: MouseEvent<HTMLButtonElement>) => void;
  type?: 'button' | 'submit' | 'reset';
  form?: string;
}

// components/ui/Button/Button.tsx
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({
    children,
    variant = 'primary',
    size = 'md',
    loading = false,
    disabled = false,
    leftIcon,
    rightIcon,
    className,
    onClick,
    testId,
    ...props
  }, ref) => {
    // Prepare styles based on props
    const buttonStyles = useMemo(() => {
      const baseStyles = 'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50';

      const variants = {
        primary: 'bg-primary text-primary-foreground hover:bg-primary/90',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
      };

      const sizes = {
        sm: 'h-9 px-3 text-sm',
        md: 'h-10 px-4 py-2',
        lg: 'h-11 px-8 text-lg',
      };

      return cn(baseStyles, variants[variant], sizes[size], className);
    }, [variant, size, className]);

    const handleClick = useCallback((event: MouseEvent<HTMLButtonElement>) => {
      if (!loading && !disabled && onClick) {
        onClick(event);
      }
    }, [loading, disabled, onClick]);

    return (
      <button
        ref={ref}
        className={buttonStyles}
        disabled={disabled || loading}
        onClick={handleClick}
        data-testid={testId}
        {...props}
      >
        {loading && <LoadingSpinner className="mr-2 h-4 w-4" />}
        {!loading && leftIcon && <span className="mr-2">{leftIcon}</span>}
        {children}
        {!loading && rightIcon && <span className="ml-2">{rightIcon}</span>}
      </button>
    );
  }
);

Button.displayName = 'Button';

// components/ui/Button/index.ts
export { Button } from './Button';
export type { ButtonProps } from './Button.types';
```

#### Feature Component Pattern
```typescript
// components/features/UserManagement/components/UserList/UserList.types.ts
export interface UserListProps extends FeatureComponentProps {
  filters?: UserFilters;
  onUserSelect?: (user: User) => void;
  onUserEdit?: (user: User) => void;
  onUserDelete?: (userId: string) => void;
  selectable?: boolean;
  showActions?: boolean;
}

export interface PreparedUserData {
  id: string;
  displayName: string;
  email: string;
  roleDisplay: string;
  statusBadge: {
    variant: 'success' | 'warning' | 'destructive';
    text: string;
  };
  lastLoginFormatted: string;
  avatarUrl?: string;
}

// components/features/UserManagement/components/UserList/UserList.tsx
export function UserList({
  filters,
  onUserSelect,
  onUserEdit,
  onUserDelete,
  selectable = false,
  showActions = true,
  loading = false,
  error = null,
  className,
  testId = 'user-list',
}: UserListProps) {
  // Get data from context
  const { users, isLoading, error: contextError } = useUsers(filters);

  // Combine loading states
  const isDataLoading = loading || isLoading;
  const displayError = error || contextError;

  // Prepare data for display - CRITICAL: Do this in useMemo, not in JSX
  const preparedUsers = useMemo((): PreparedUserData[] => {
    if (!users?.users) return [];

    return users.users.map(user => ({
      id: user.id,
      displayName: `${user.firstName} ${user.lastName}`,
      email: user.email,
      roleDisplay: formatUserRole(user.role),
      statusBadge: getUserStatusBadge(user.status),
      lastLoginFormatted: user.lastLoginAt
        ? formatDistanceToNow(new Date(user.lastLoginAt), { addSuffix: true })
        : 'Never',
      avatarUrl: user.avatar,
    }));
  }, [users?.users]);

  // Memoize event handlers
  const handleUserClick = useCallback((user: PreparedUserData) => {
    if (selectable && onUserSelect) {
      // Find original user object
      const originalUser = users?.users.find(u => u.id === user.id);
      if (originalUser) {
        onUserSelect(originalUser);
      }
    }
  }, [selectable, onUserSelect, users?.users]);

  const handleEditClick = useCallback((user: PreparedUserData) => {
    if (onUserEdit) {
      const originalUser = users?.users.find(u => u.id === user.id);
      if (originalUser) {
        onUserEdit(originalUser);
      }
    }
  }, [onUserEdit, users?.users]);

  const handleDeleteClick = useCallback((userId: string) => {
    if (onUserDelete) {
      onUserDelete(userId);
    }
  }, [onUserDelete]);

  // Loading state
  if (isDataLoading) {
    return (
      <div className={cn('space-y-4', className)} data-testid={`${testId}-loading`}>
        {Array.from({ length: 5 }).map((_, i) => (
          <UserListItemSkeleton key={i} />
        ))}
      </div>
    );
  }

  // Error state
  if (displayError) {
    return (
      <ErrorMessage
        message={displayError}
        onRetry={() => window.location.reload()}
        className={className}
        data-testid={`${testId}-error`}
      />
    );
  }

  // Empty state
  if (preparedUsers.length === 0) {
    return (
      <EmptyState
        title="No users found"
        description="Try adjusting your filters or create a new user."
        action={
          <Button onClick={() => {}}>
            Create User
          </Button>
        }
        className={className}
        data-testid={`${testId}-empty`}
      />
    );
  }

  // Main render - clean JSX using prepared data
  return (
    <div className={cn('space-y-2', className)} data-testid={testId}>
      {preparedUsers.map(user => (
        <UserListItem
          key={user.id}
          user={user}
          selectable={selectable}
          showActions={showActions}
          onClick={() => handleUserClick(user)}
          onEdit={() => handleEditClick(user)}
          onDelete={() => handleDeleteClick(user.id)}
        />
      ))}
    </div>
  );
}

// Helper functions for data preparation
function formatUserRole(role: UserRole): string {
  const roleLabels = {
    [UserRole.ADMIN]: 'Administrator',
    [UserRole.MANAGER]: 'Manager',
    [UserRole.USER]: 'User',
    [UserRole.GUEST]: 'Guest',
  };
  return roleLabels[role];
}

function getUserStatusBadge(status: UserStatus): { variant: 'success' | 'warning' | 'destructive'; text: string } {
  const statusConfig = {
    [UserStatus.ACTIVE]: { variant: 'success' as const, text: 'Active' },
    [UserStatus.INACTIVE]: { variant: 'warning' as const, text: 'Inactive' },
    [UserStatus.SUSPENDED]: { variant: 'destructive' as const, text: 'Suspended' },
    [UserStatus.PENDING]: { variant: 'warning' as const, text: 'Pending' },
  };
  return statusConfig[status];
}
```

---

## 📊 Data Preparation Pattern

### The useMemo Rule %%PRIORITY:HIGH%%

#### ✅ Correct: Data Preparation Before Render
```typescript
function OrdersTable({ orders, filters }: OrdersTableProps) {
  // ✅ CORRECT - All data transformation in useMemo
  const preparedOrders = useMemo(() => {
    if (!orders) return [];

    // Apply filters
    let filtered = orders;
    if (filters.status) {
      filtered = filtered.filter(order => order.status === filters.status);
    }
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(order =>
        order.customer.name.toLowerCase().includes(searchLower) ||
        order.id.toLowerCase().includes(searchLower)
      );
    }

    // Sort data
    if (filters.sortBy) {
      filtered = [...filtered].sort((a, b) => {
        const aValue = a[filters.sortBy!];
        const bValue = b[filters.sortBy!];
        const modifier = filters.sortOrder === 'desc' ? -1 : 1;

        if (aValue < bValue) return -1 * modifier;
        if (aValue > bValue) return 1 * modifier;
        return 0;
      });
    }

    // Transform for display
    return filtered.map(order => ({
      ...order,
      displayId: `#${order.id.slice(-6)}`,
      customerName: order.customer.name,
      statusBadge: getOrderStatusBadge(order.status),
      formattedDate: format(new Date(order.createdAt), 'MMM dd, yyyy'),
      formattedTotal: formatCurrency(order.total, order.currency),
      itemCount: order.items.length,
    }));
  }, [orders, filters]);

  const tableStats = useMemo(() => ({
    totalOrders: preparedOrders.length,
    totalValue: preparedOrders.reduce((sum, order) => sum + order.total, 0),
    averageValue: preparedOrders.length > 0
      ? preparedOrders.reduce((sum, order) => sum + order.total, 0) / preparedOrders.length
      : 0,
  }), [preparedOrders]);

  return (
    <div>
      <TableStats stats={tableStats} />
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Order ID</TableHead>
            <TableHead>Customer</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Date</TableHead>
            <TableHead>Total</TableHead>
            <TableHead>Items</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {preparedOrders.map(order => (
            <TableRow key={order.id}>
              <TableCell>{order.displayId}</TableCell>
              <TableCell>{order.customerName}</TableCell>
              <TableCell>
                <Badge variant={order.statusBadge.variant}>
                  {order.statusBadge.text}
                </Badge>
              </TableCell>
              <TableCell>{order.formattedDate}</TableCell>
              <TableCell>{order.formattedTotal}</TableCell>
              <TableCell>{order.itemCount}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
```

#### ❌ Wrong: Data Transformation in JSX
```typescript
function OrdersTable({ orders, filters }: OrdersTableProps) {
  // ❌ FORBIDDEN - Logic and transformations in render
  return (
    <Table>
      <TableBody>
        {orders
          ?.filter(order =>
            !filters.status || order.status === filters.status
          )
          ?.filter(order =>
            !filters.search ||
            order.customer.name.toLowerCase().includes(filters.search.toLowerCase()) ||
            order.id.toLowerCase().includes(filters.search.toLowerCase())
          )
          ?.sort((a, b) => {
            if (!filters.sortBy) return 0;
            const aValue = a[filters.sortBy];
            const bValue = b[filters.sortBy];
            return filters.sortOrder === 'desc' ? bValue - aValue : aValue - bValue;
          })
          ?.map(order => (
            <TableRow key={order.id}>
              <TableCell>#{order.id.slice(-6)}</TableCell>
              <TableCell>{order.customer.name}</TableCell>
              <TableCell>
                <Badge variant={
                  order.status === 'completed' ? 'success' :
                  order.status === 'pending' ? 'warning' : 'destructive'
                }>
                  {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                </Badge>
              </TableCell>
              <TableCell>
                {format(new Date(order.createdAt), 'MMM dd, yyyy')}
              </TableCell>
              <TableCell>
                {new Intl.NumberFormat('en-US', {
                  style: 'currency',
                  currency: order.currency
                }).format(order.total)}
              </TableCell>
              <TableCell>{order.items.length}</TableCell>
            </TableRow>
          ))}
      </TableBody>
    </Table>
  );
}
```

### Complex Data Preparation Examples

#### Multi-Level Data Transformation
```typescript
function DashboardOverview({ data }: DashboardOverviewProps) {
  const dashboardData = useMemo(() => {
    if (!data) return null;

    // Calculate metrics
    const totalRevenue = data.orders.reduce((sum, order) => sum + order.total, 0);
    const totalOrders = data.orders.length;
    const avgOrderValue = totalOrders > 0 ? totalRevenue / totalOrders : 0;

    // Group orders by status
    const ordersByStatus = data.orders.reduce((acc, order) => {
      acc[order.status] = (acc[order.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    // Calculate growth rates
    const previousPeriod = data.previousPeriod;
    const revenueGrowth = previousPeriod?.revenue
      ? ((totalRevenue - previousPeriod.revenue) / previousPeriod.revenue) * 100
      : 0;

    // Prepare chart data
    const chartData = data.dailyStats.map(stat => ({
      date: format(new Date(stat.date), 'MMM dd'),
      revenue: stat.revenue,
      orders: stat.orderCount,
      avgOrderValue: stat.orderCount > 0 ? stat.revenue / stat.orderCount : 0,
    }));

    // Top products
    const topProducts = data.products
      .sort((a, b) => b.salesCount - a.salesCount)
      .slice(0, 5)
      .map(product => ({
        ...product,
        salesFormatted: formatNumber(product.salesCount),
        revenueFormatted: formatCurrency(product.revenue),
      }));

    return {
      metrics: {
        totalRevenue: formatCurrency(totalRevenue),
        totalOrders: formatNumber(totalOrders),
        avgOrderValue: formatCurrency(avgOrderValue),
        revenueGrowth: {
          value: revenueGrowth,
          formatted: `${revenueGrowth >= 0 ? '+' : ''}${revenueGrowth.toFixed(1)}%`,
          isPositive: revenueGrowth >= 0,
        },
      },
      ordersByStatus,
      chartData,
      topProducts,
    };
  }, [data]);

  if (!dashboardData) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="space-y-6">
      <MetricsGrid metrics={dashboardData.metrics} />
      <OrderStatusChart data={dashboardData.ordersByStatus} />
      <RevenueChart data={dashboardData.chartData} />
      <TopProductsList products={dashboardData.topProducts} />
    </div>
  );
}
```

---

## 🔄 Context Over Props

### Context Pattern Implementation

#### Feature Context Pattern
```typescript
// contexts/UserManagementContext.tsx
interface UserManagementState {
  users: UserListResponse | null;
  selectedUser: User | null;
  filters: UserFilters;
  isLoading: boolean;
  error: string | null;
}

interface UserManagementActions {
  setFilters: (filters: UserFilters) => void;
  selectUser: (user: User | null) => void;
  createUser: (userData: CreateUserRequest) => Promise<User>;
  updateUser: (userId: string, updates: UpdateUserRequest) => Promise<User>;
  deleteUser: (userId: string) => Promise<void>;
  refreshUsers: () => Promise<void>;
}

type UserManagementContextType = UserManagementState & UserManagementActions;

const UserManagementContext = createContext<UserManagementContextType | undefined>(undefined);

export function UserManagementProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<UserManagementState>({
    users: null,
    selectedUser: null,
    filters: {},
    isLoading: false,
    error: null,
  });

  // Load users when filters change
  useEffect(() => {
    loadUsers();
  }, [state.filters]);

  const loadUsers = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const users = await UserService.getUsers(state.filters);
      setState(prev => ({ ...prev, users, isLoading: false }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to load users'
      }));
    }
  }, [state.filters]);

  const setFilters = useCallback((filters: UserFilters) => {
    setState(prev => ({ ...prev, filters }));
  }, []);

  const selectUser = useCallback((user: User | null) => {
    setState(prev => ({ ...prev, selectedUser: user }));
  }, []);

  const createUser = useCallback(async (userData: CreateUserRequest): Promise<User> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const newUser = await UserService.createUser(userData);

      // Optimistically update the users list
      setState(prev => ({
        ...prev,
        isLoading: false,
        users: prev.users ? {
          ...prev.users,
          users: [...prev.users.users, newUser],
        } : null,
      }));

      return newUser;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to create user'
      }));
      throw error;
    }
  }, []);

  const updateUser = useCallback(async (userId: string, updates: UpdateUserRequest): Promise<User> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const updatedUser = await UserService.updateUser(userId, updates);

      setState(prev => ({
        ...prev,
        isLoading: false,
        users: prev.users ? {
          ...prev.users,
          users: prev.users.users.map(user =>
            user.id === userId ? updatedUser : user
          ),
        } : null,
        selectedUser: prev.selectedUser?.id === userId ? updatedUser : prev.selectedUser,
      }));

      return updatedUser;
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to update user'
      }));
      throw error;
    }
  }, []);

  const deleteUser = useCallback(async (userId: string): Promise<void> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      await UserService.deleteUser(userId);

      setState(prev => ({
        ...prev,
        isLoading: false,
        users: prev.users ? {
          ...prev.users,
          users: prev.users.users.filter(user => user.id !== userId),
        } : null,
        selectedUser: prev.selectedUser?.id === userId ? null : prev.selectedUser,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to delete user'
      }));
      throw error;
    }
  }, []);

  const refreshUsers = useCallback(async () => {
    await loadUsers();
  }, [loadUsers]);

  const value = useMemo((): UserManagementContextType => ({
    ...state,
    setFilters,
    selectUser,
    createUser,
    updateUser,
    deleteUser,
    refreshUsers,
  }), [state, setFilters, selectUser, createUser, updateUser, deleteUser, refreshUsers]);

  return (
    <UserManagementContext.Provider value={value}>
      {children}
    </UserManagementContext.Provider>
  );
}

export function useUserManagement(): UserManagementContextType {
  const context = useContext(UserManagementContext);
  if (context === undefined) {
    throw new Error('useUserManagement must be used within a UserManagementProvider');
  }
  return context;
}
```

#### Component Using Context (No Props)
```typescript
// ✅ CORRECT - Components access context directly
function UserList() {
  const { users, isLoading, error, selectUser } = useUserManagement();

  // Component logic using context data directly
  const handleUserClick = useCallback((user: User) => {
    selectUser(user);
  }, [selectUser]);

  // ... rest of component
}

function UserFilters() {
  const { filters, setFilters } = useUserManagement();

  // Component uses context directly
  const handleFilterChange = useCallback((newFilters: UserFilters) => {
    setFilters(newFilters);
  }, [setFilters]);

  // ... rest of component
}

function UserDetails() {
  const { selectedUser, updateUser } = useUserManagement();

  // Component accesses selected user from context
  if (!selectedUser) {
    return <div>No user selected</div>;
  }

  // ... rest of component
}

// ❌ WRONG - Passing context data as props
function UserManagementPage() {
  const { users, isLoading, error, selectedUser } = useUserManagement();

  // Don't pass context data as props!
  return (
    <div>
      <UserList users={users} loading={isLoading} error={error} /> {/* WRONG */}
      <UserDetails user={selectedUser} /> {/* WRONG */}
    </div>
  );
}

// ✅ CORRECT - Let components access context directly
function UserManagementPage() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <UserFilters />
        <UserList />
      </div>
      <div>
        <UserDetails />
      </div>
    </div>
  );
}
```

---

## 🧠 State Management

### Local State with useState and useReducer

#### Simple State Management
```typescript
function UserForm({ user, onSave, onCancel }: UserFormProps) {
  // Form state
  const [formData, setFormData] = useState<CreateUserRequest>({
    email: user?.email || '',
    firstName: user?.firstName || '',
    lastName: user?.lastName || '',
    password: '',
    role: user?.role || UserRole.USER,
  });

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isDirty, setIsDirty] = useState(false);

  // Memoized validation
  const validationErrors = useMemo(() => {
    const errors: Record<string, string> = {};

    if (!formData.email) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      errors.email = 'Email is invalid';
    }

    if (!formData.firstName) {
      errors.firstName = 'First name is required';
    }

    if (!formData.lastName) {
      errors.lastName = 'Last name is required';
    }

    if (!user && !formData.password) {
      errors.password = 'Password is required';
    } else if (!user && formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    }

    return errors;
  }, [formData, user]);

  const isValid = useMemo(() => {
    return Object.keys(validationErrors).length === 0;
  }, [validationErrors]);

  // Update form data
  const updateField = useCallback(<K extends keyof CreateUserRequest>(
    field: K,
    value: CreateUserRequest[K]
  ) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setIsDirty(true);

    // Clear field error when user starts typing
    if (errors[field]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  }, [errors]);

  // Submit handler
  const handleSubmit = useCallback(async (e: FormEvent) => {
    e.preventDefault();

    if (!isValid) {
      setErrors(validationErrors);
      return;
    }

    setIsSubmitting(true);

    try {
      await onSave(formData);
    } catch (error) {
      setErrors({
        submit: error instanceof Error ? error.message : 'Failed to save user'
      });
    } finally {
      setIsSubmitting(false);
    }
  }, [formData, isValid, validationErrors, onSave]);

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        label="Email"
        type="email"
        value={formData.email}
        onChange={(value) => updateField('email', value)}
        error={errors.email}
        required
      />

      <Input
        label="First Name"
        value={formData.firstName}
        onChange={(value) => updateField('firstName', value)}
        error={errors.firstName}
        required
      />

      <Input
        label="Last Name"
        value={formData.lastName}
        onChange={(value) => updateField('lastName', value)}
        error={errors.lastName}
        required
      />

      {!user && (
        <Input
          label="Password"
          type="password"
          value={formData.password}
          onChange={(value) => updateField('password', value)}
          error={errors.password}
          required
        />
      )}

      <Select
        label="Role"
        value={formData.role}
        onChange={(value) => updateField('role', value as UserRole)}
        options={Object.values(UserRole).map(role => ({
          value: role,
          label: formatUserRole(role),
        }))}
      />

      {errors.submit && (
        <Alert variant="destructive">
          <AlertDescription>{errors.submit}</AlertDescription>
        </Alert>
      )}

      <div className="flex justify-end space-x-2">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button
          type="submit"
          loading={isSubmitting}
          disabled={!isDirty || !isValid}
        >
          {user ? 'Update' : 'Create'} User
        </Button>
      </div>
    </form>
  );
}
```

#### Complex State with useReducer
```typescript
// For complex state logic, use useReducer
interface FilterState {
  search: string;
  role: UserRole | null;
  status: UserStatus | null;
  dateRange: {
    from: Date | null;
    to: Date | null;
  };
  sortBy: SortField | null;
  sortOrder: 'asc' | 'desc';
  page: number;
  limit: number;
}

type FilterAction =
  | { type: 'SET_SEARCH'; payload: string }
  | { type: 'SET_ROLE'; payload: UserRole | null }
  | { type: 'SET_STATUS'; payload: UserStatus | null }
  | { type: 'SET_DATE_RANGE'; payload: { from: Date | null; to: Date | null } }
  | { type: 'SET_SORT'; payload: { field: SortField; order: 'asc' | 'desc' } }
  | { type: 'SET_PAGE'; payload: number }
  | { type: 'SET_LIMIT'; payload: number }
  | { type: 'RESET_FILTERS' }
  | { type: 'CLEAR_SEARCH' };

function filterReducer(state: FilterState, action: FilterAction): FilterState {
  switch (action.type) {
    case 'SET_SEARCH':
      return { ...state, search: action.payload, page: 1 };

    case 'SET_ROLE':
      return { ...state, role: action.payload, page: 1 };

    case 'SET_STATUS':
      return { ...state, status: action.payload, page: 1 };

    case 'SET_DATE_RANGE':
      return { ...state, dateRange: action.payload, page: 1 };

    case 'SET_SORT':
      return {
        ...state,
        sortBy: action.payload.field,
        sortOrder: action.payload.order
      };

    case 'SET_PAGE':
      return { ...state, page: action.payload };

    case 'SET_LIMIT':
      return { ...state, limit: action.payload, page: 1 };

    case 'RESET_FILTERS':
      return initialFilterState;

    case 'CLEAR_SEARCH':
      return { ...state, search: '', page: 1 };

    default:
      return state;
  }
}

const initialFilterState: FilterState = {
  search: '',
  role: null,
  status: null,
  dateRange: { from: null, to: null },
  sortBy: null,
  sortOrder: 'asc',
  page: 1,
  limit: 20,
};

function useUserFilters() {
  const [state, dispatch] = useReducer(filterReducer, initialFilterState);

  const actions = useMemo(() => ({
    setSearch: (search: string) => dispatch({ type: 'SET_SEARCH', payload: search }),
    setRole: (role: UserRole | null) => dispatch({ type: 'SET_ROLE', payload: role }),
    setStatus: (status: UserStatus | null) => dispatch({ type: 'SET_STATUS', payload: status }),
    setDateRange: (dateRange: { from: Date | null; to: Date | null }) =>
      dispatch({ type: 'SET_DATE_RANGE', payload: dateRange }),
    setSort: (field: SortField, order: 'asc' | 'desc') =>
      dispatch({ type: 'SET_SORT', payload: { field, order } }),
    setPage: (page: number) => dispatch({ type: 'SET_PAGE', payload: page }),
    setLimit: (limit: number) => dispatch({ type: 'SET_LIMIT', payload: limit }),
    resetFilters: () => dispatch({ type: 'RESET_FILTERS' }),
    clearSearch: () => dispatch({ type: 'CLEAR_SEARCH' }),
  }), []);

  return { state, actions };
}
```

---

## ⚡ Performance Optimization

### Memoization Patterns

#### Component Memoization
```typescript
// Memoize expensive components
const UserListItem = memo<UserListItemProps>(({
  user,
  onEdit,
  onDelete,
  selectable,
  selected
}) => {
  // Component implementation
  return (
    <div className={cn('p-4 border rounded-lg', selected && 'bg-blue-50')}>
      {/* Component content */}
    </div>
  );
});

// Custom comparison function for complex props
const UserCard = memo<UserCardProps>(({ user, actions }) => {
  // Component implementation
}, (prevProps, nextProps) => {
  // Custom comparison
  return (
    prevProps.user.id === nextProps.user.id &&
    prevProps.user.updatedAt === nextProps.user.updatedAt &&
    prevProps.actions === nextProps.actions // Reference equality for actions
  );
});
```

#### Callback Memoization
```typescript
function UserManagement() {
  const { users, updateUser, deleteUser } = useUserManagement();

  // Memoize callback functions
  const handleUserEdit = useCallback((user: User) => {
    // Edit logic
    router.push(`/users/${user.id}/edit`);
  }, [router]);

  const handleUserDelete = useCallback(async (userId: string) => {
    if (confirm('Are you sure you want to delete this user?')) {
      await deleteUser(userId);
    }
  }, [deleteUser]);

  // Memoize props object to prevent unnecessary re-renders
  const listActions = useMemo(() => ({
    onEdit: handleUserEdit,
    onDelete: handleUserDelete,
  }), [handleUserEdit, handleUserDelete]);

  return (
    <UserList users={users} actions={listActions} />
  );
}
```

### Virtual Scrolling for Large Lists

#### React Window Integration
```typescript
import { FixedSizeList as List } from 'react-window';

interface VirtualUserListProps {
  users: User[];
  onUserSelect: (user: User) => void;
}

function VirtualUserList({ users, onUserSelect }: VirtualUserListProps) {
  // Memoize item data to prevent unnecessary re-renders
  const itemData = useMemo(() => ({
    users,
    onUserSelect,
  }), [users, onUserSelect]);

  return (
    <List
      height={400}
      itemCount={users.length}
      itemSize={60}
      itemData={itemData}
    >
      {UserListItemRenderer}
    </List>
  );
}

// Memoized item renderer
const UserListItemRenderer = memo<ListChildComponentProps<{
  users: User[];
  onUserSelect: (user: User) => void;
}>>(({ index, style, data }) => {
  const user = data.users[index];

  const handleClick = useCallback(() => {
    data.onUserSelect(user);
  }, [user, data.onUserSelect]);

  return (
    <div style={style} className="px-4 py-2 border-b cursor-pointer hover:bg-gray-50">
      <div onClick={handleClick}>
        <div className="font-medium">{user.firstName} {user.lastName}</div>
        <div className="text-sm text-gray-500">{user.email}</div>
      </div>
    </div>
  );
});
```

---

## 🧪 Component Testing

### Testing Patterns

#### Component with Context Testing
```typescript
// __tests__/UserList.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { UserManagementProvider } from '@/contexts/UserManagementContext';
import { UserList } from '@/components/features/UserManagement/UserList';

// Mock the service
jest.mock('@/services/userService');

const renderWithProvider = (ui: ReactElement) => {
  return render(
    <UserManagementProvider>
      {ui}
    </UserManagementProvider>
  );
};

describe('UserList', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
  });

  it('displays loading state initially', () => {
    renderWithProvider(<UserList />);

    expect(screen.getByTestId('user-list-loading')).toBeInTheDocument();
  });

  it('displays users when loaded', async () => {
    const mockUsers = [
      { id: '1', firstName: 'John', lastName: 'Doe', email: 'john@example.com' },
      { id: '2', firstName: 'Jane', lastName: 'Smith', email: 'jane@example.com' },
    ];

    UserService.getUsers.mockResolvedValue({ users: mockUsers });

    renderWithProvider(<UserList />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });
  });

  it('handles user selection', async () => {
    const mockUsers = [
      { id: '1', firstName: 'John', lastName: 'Doe', email: 'john@example.com' },
    ];

    UserService.getUsers.mockResolvedValue({ users: mockUsers });

    renderWithProvider(<UserList selectable />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('John Doe'));

    // Test that user was selected (would need to check context state)
  });

  it('displays error message when loading fails', async () => {
    UserService.getUsers.mockRejectedValue(new Error('Failed to load users'));

    renderWithProvider(<UserList />);

    await waitFor(() => {
      expect(screen.getByTestId('user-list-error')).toBeInTheDocument();
      expect(screen.getByText(/Failed to load users/)).toBeInTheDocument();
    });
  });
});
```

#### Testing Data Preparation
```typescript
// __tests__/userDataPreparation.test.ts
import { prepareUserData } from '@/components/features/UserManagement/UserList';

describe('User Data Preparation', () => {
  it('formats user data correctly', () => {
    const rawUsers = [
      {
        id: '1',
        firstName: 'John',
        lastName: 'Doe',
        email: 'john@example.com',
        role: UserRole.ADMIN,
        status: UserStatus.ACTIVE,
        lastLoginAt: '2023-12-01T10:00:00Z',
      },
    ];

    const prepared = prepareUserData(rawUsers);

    expect(prepared[0]).toEqual({
      id: '1',
      displayName: 'John Doe',
      email: 'john@example.com',
      roleDisplay: 'Administrator',
      statusBadge: {
        variant: 'success',
        text: 'Active',
      },
      lastLoginFormatted: expect.stringContaining('ago'),
    });
  });

  it('handles users with no last login', () => {
    const rawUsers = [
      {
        id: '1',
        firstName: 'John',
        lastName: 'Doe',
        email: 'john@example.com',
        role: UserRole.USER,
        status: UserStatus.PENDING,
        lastLoginAt: null,
      },
    ];

    const prepared = prepareUserData(rawUsers);

    expect(prepared[0].lastLoginFormatted).toBe('Never');
  });
});
```

---

## 🏷️ Metadata
**Framework**: Next.js 13+ with React 18+
**Patterns**: Data Preparation, Context Over Props, Memoization
**Performance**: useMemo, useCallback, React.memo, Virtual Scrolling
**Testing**: React Testing Library, Context Testing
**Type Safety**: Full TypeScript coverage

%%AI_HINT: These component patterns ensure maintainable, performant, and testable React components in Next.js applications%%
