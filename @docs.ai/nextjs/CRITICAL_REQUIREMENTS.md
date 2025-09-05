# 🚨 Next.js Critical Requirements %%PRIORITY:HIGH%%

## 🎯 Quick Summary
Non-negotiable patterns and zero-tolerance violations for Next.js development. These requirements ensure maintainable, performant, and AI-friendly codebases.

## 📋 Table of Contents
1. [Zero Tolerance Violations](#zero-tolerance-violations)
2. [Mandatory Patterns](#mandatory-patterns)
3. [Architecture Principles](#architecture-principles)
4. [Data Flow Patterns](#data-flow-patterns)
5. [Component Guidelines](#component-guidelines)
6. [Quality Gates](#quality-gates)

## 🔑 Key Principles at a Glance
- **KISS Methodology**: Simple solutions over complex abstractions
- **Type Safety**: 100% TypeScript coverage, zero `any` types
- **Data Preparation**: Transform data before render, never in JSX
- **Context Over Props**: Use React Context instead of prop drilling
- **Service Layer**: All API calls through dedicated service classes
- **Error Handling**: Consistent error boundaries and loading states

---

## 🚨 Zero Tolerance Violations

### ❌ Type Safety Violations

#### Raw Any/Unknown Usage
```typescript
// ❌ FORBIDDEN - Any type usage
const data: any = response;
const config: any = {};
function process(input: any): any { }

// ❌ FORBIDDEN - As any casting
const result = response as any;
const config = settings as any;

// ✅ CORRECT - Proper typing
const data: ApiResponse = response;
const config: AppConfig = {};
function process(input: ProcessInput): ProcessOutput { }

// ✅ CORRECT - Safe type casting
const result = response as ApiResponse;
const config = settings as AppConfig;
```

#### Missing Type Annotations
```typescript
// ❌ FORBIDDEN - Missing types
export function fetchData(url) {
  return fetch(url);
}

const handler = (event) => {
  console.log(event);
};

// ✅ CORRECT - Complete type annotations
export function fetchData(url: string): Promise<Response> {
  return fetch(url);
}

const handler = (event: MouseEvent) => {
  console.log(event);
};
```

### ❌ Component Anti-Patterns

#### Data Transformation in JSX
```typescript
// ❌ FORBIDDEN - Logic in render
function UserList({ users }) {
  return (
    <div>
      {users?.filter(u => u.active)
             ?.map(u => ({ ...u, displayName: `${u.firstName} ${u.lastName}` }))
             ?.slice(0, 10)
             ?.map(user => (
        <div key={user.id}>
          {user.displayName} - {user.isActive ? 'Active' : 'Inactive'}
        </div>
      ))}
    </div>
  );
}

// ✅ CORRECT - Data preparation with useMemo
function UserList({ users }: { users: User[] }) {
  const preparedUsers = useMemo(() => {
    if (!users) return [];

    return users
      .filter(user => user.active)
      .map(user => ({
        ...user,
        displayName: `${user.firstName} ${user.lastName}`,
        statusText: user.isActive ? 'Active' : 'Inactive'
      }))
      .slice(0, 10);
  }, [users]);

  return (
    <div>
      {preparedUsers.map(user => (
        <div key={user.id}>
          {user.displayName} - {user.statusText}
        </div>
      ))}
    </div>
  );
}
```

#### Prop Drilling
```typescript
// ❌ FORBIDDEN - Prop drilling through multiple levels
function App() {
  const user = useAuth();
  const theme = useTheme();

  return <Layout user={user} theme={theme} />;
}

function Layout({ user, theme, children }) {
  return <Sidebar user={user} theme={theme}>{children}</Sidebar>;
}

function Sidebar({ user, theme }) {
  return <UserMenu user={user} theme={theme} />;
}

// ✅ CORRECT - Context usage
function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <Layout />
      </ThemeProvider>
    </AuthProvider>
  );
}

function Sidebar() {
  return <UserMenu />; // No props needed
}

function UserMenu() {
  const { user } = useAuth();    // Direct context access
  const { theme } = useTheme();  // Direct context access

  return <div>{user.name}</div>;
}
```

### ❌ API Integration Violations

#### Direct API Calls in Components
```typescript
// ❌ FORBIDDEN - Direct fetch in component
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then(res => res.json())
      .then(setUser)
      .catch(console.error);
  }, [userId]);

  return <div>{user?.name}</div>;
}

// ✅ CORRECT - Service layer
// services/userService.ts
export class UserService {
  static async getUser(userId: string): Promise<User> {
    const response = await fetch(`/api/users/${userId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch user: ${response.statusText}`);
    }
    return response.json();
  }
}

// components/UserProfile.tsx
function UserProfile({ userId }: { userId: string }) {
  const [user, setUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    UserService.getUser(userId)
      .then(setUser)
      .catch(err => setError(err.message));
  }, [userId]);

  if (error) return <div>Error: {error}</div>;
  return <div>{user?.name}</div>;
}
```

### ❌ File Organization Violations

#### Relative Import Chaos
```typescript
// ❌ FORBIDDEN - Deep relative imports
import { UserService } from '../../../services/user';
import { validateEmail } from '../../../../utils/validation';
import { Button } from '../../../../../../components/ui/Button';

// ✅ CORRECT - Absolute imports with aliases
import { UserService } from '@/services/user';
import { validateEmail } from '@/utils/validation';
import { Button } from '@/components/ui/Button';
```

#### Mixed Concerns in Files
```typescript
// ❌ FORBIDDEN - Mixed concerns in single file
// pages/dashboard.tsx (500+ lines)
export default function Dashboard() {
  // API calls
  const fetchStats = async () => { /* ... */ };

  // Business logic
  const calculateMetrics = () => { /* ... */ };

  // UI components
  const StatsCard = () => { /* ... */ };
  const MetricsChart = () => { /* ... */ };

  // Main component with everything mixed
  return <div>{/* 300+ lines of JSX */}</div>;
}

// ✅ CORRECT - Separation of concerns
// services/statsService.ts
export class StatsService {
  static async getStats(): Promise<Stats> { /* ... */ }
}

// utils/metricsCalculator.ts
export function calculateMetrics(data: RawData): Metrics { /* ... */ }

// components/StatsCard.tsx
export function StatsCard({ stats }: { stats: Stats }) { /* ... */ }

// views/DashboardView.tsx
export function DashboardView() {
  const stats = useStats(); // Custom hook
  const metrics = useMemo(() => calculateMetrics(stats.data), [stats.data]);

  return (
    <div>
      <StatsCard stats={stats} />
      <MetricsChart metrics={metrics} />
    </div>
  );
}

// pages/dashboard.tsx
export default function DashboardPage() {
  return <DashboardView />;
}
```

---

## ✅ Mandatory Patterns

### ✅ Service Layer Architecture

#### API Service Pattern
```typescript
// services/baseService.ts
export abstract class BaseService {
  protected static baseURL = process.env.NEXT_PUBLIC_API_URL || '';

  protected static async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }
}

// services/userService.ts
export class UserService extends BaseService {
  static async getUsers(): Promise<User[]> {
    return this.request<User[]>('/api/users');
  }

  static async createUser(userData: CreateUserRequest): Promise<User> {
    return this.request<User>('/api/users', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  static async updateUser(id: string, updates: UpdateUserRequest): Promise<User> {
    return this.request<User>(`/api/users/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }
}
```

### ✅ Context Pattern for State Management

#### Typed Context Implementation
```typescript
// contexts/AuthContext.tsx
interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface AuthActions {
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

type AuthContextType = AuthState & AuthActions;

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
  });

  const login = useCallback(async (email: string, password: string) => {
    setState(prev => ({ ...prev, isLoading: true }));

    try {
      const user = await AuthService.login({ email, password });
      setState({
        user,
        isLoading: false,
        isAuthenticated: true,
      });
      return true;
    } catch (error) {
      setState(prev => ({ ...prev, isLoading: false }));
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    AuthService.logout();
    setState({
      user: null,
      isLoading: false,
      isAuthenticated: false,
    });
  }, []);

  const value = useMemo(() => ({
    ...state,
    login,
    logout,
    refreshUser,
  }), [state, login, logout, refreshUser]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

### ✅ Data Preparation Pattern

#### useMemo for Data Transformation
```typescript
// ✅ CORRECT - Comprehensive data preparation
function OrdersTable({ orders, filters }: OrdersTableProps) {
  const preparedOrders = useMemo(() => {
    if (!orders) return [];

    // Apply filters
    let filtered = orders;
    if (filters.status) {
      filtered = filtered.filter(order => order.status === filters.status);
    }
    if (filters.dateRange) {
      filtered = filtered.filter(order =>
        isWithinDateRange(order.createdAt, filters.dateRange)
      );
    }

    // Transform data for display
    return filtered.map(order => ({
      ...order,
      displayId: `#${order.id.slice(-6)}`,
      statusBadge: getStatusBadgeProps(order.status),
      formattedDate: formatDate(order.createdAt),
      formattedTotal: formatCurrency(order.total),
      customerName: `${order.customer.firstName} ${order.customer.lastName}`,
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
      <TableHeader stats={tableStats} />
      <Table>
        {preparedOrders.map(order => (
          <TableRow key={order.id}>
            <TableCell>{order.displayId}</TableCell>
            <TableCell>{order.customerName}</TableCell>
            <TableCell>
              <Badge {...order.statusBadge}>{order.status}</Badge>
            </TableCell>
            <TableCell>{order.formattedDate}</TableCell>
            <TableCell>{order.formattedTotal}</TableCell>
          </TableRow>
        ))}
      </Table>
    </div>
  );
}
```

### ✅ Error Handling Pattern

#### Error Boundaries and Consistent Error States
```typescript
// components/ErrorBoundary.tsx
interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<
  { children: ReactNode; fallback?: ComponentType<{ error: Error }> },
  ErrorBoundaryState
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error Boundary caught an error:', error, errorInfo);
    // Send to error reporting service
  }

  render() {
    if (this.state.hasError) {
      const FallbackComponent = this.props.fallback || DefaultErrorFallback;
      return <FallbackComponent error={this.state.error!} />;
    }

    return this.props.children;
  }
}

// hooks/useAsyncOperation.ts
export function useAsyncOperation<T>() {
  const [state, setState] = useState<{
    data: T | null;
    loading: boolean;
    error: string | null;
  }>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(async (operation: () => Promise<T>) => {
    setState({ data: null, loading: true, error: null });

    try {
      const result = await operation();
      setState({ data: result, loading: false, error: null });
      return result;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setState({ data: null, loading: false, error: errorMessage });
      throw error;
    }
  }, []);

  return { ...state, execute };
}
```

---

## 🏗️ Architecture Principles

### KISS Methodology %%PRIORITY:HIGH%%

#### Simple Solutions Over Complex Abstractions
```typescript
// ❌ OVER-ENGINEERED - Unnecessary abstraction
class DataManager<T> {
  private cache = new Map<string, CacheEntry<T>>();
  private subscribers = new Set<Subscriber<T>>();

  async get<K extends keyof T>(key: K): Promise<T[K]> {
    // 50+ lines of complex caching logic
  }
}

// ✅ SIMPLE - Direct, clear approach
function useUserData(userId: string) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    UserService.getUser(userId)
      .then(setUser)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [userId]);

  return { user, loading, error };
}
```

#### Clear Intent in Code
```typescript
// ❌ UNCLEAR - Magic numbers and abbreviations
function calcUDisc(u: User, o: Order): number {
  return u.lvl > 5 ? o.amt * 0.1 : o.amt * 0.05;
}

// ✅ CLEAR - Self-documenting code
function calculateUserDiscount(user: User, order: Order): number {
  const PREMIUM_USER_LEVEL = 5;
  const PREMIUM_DISCOUNT_RATE = 0.1;
  const STANDARD_DISCOUNT_RATE = 0.05;

  const isPremiumUser = user.level > PREMIUM_USER_LEVEL;
  const discountRate = isPremiumUser ? PREMIUM_DISCOUNT_RATE : STANDARD_DISCOUNT_RATE;

  return order.amount * discountRate;
}
```

---

## 🎯 Quality Gates

### Pre-commit Checks
```bash
# Type checking (zero errors allowed)
npx tsc --noEmit

# Linting (zero errors, minimal warnings)
npm run lint

# Unit tests (100% pass rate)
npm run test

# Build verification
npm run build
```

### Code Review Requirements
- [ ] No `any` types or `as any` casts
- [ ] All components use TypeScript interfaces for props
- [ ] Data transformation handled in useMemo, not JSX
- [ ] API calls go through service layer
- [ ] Error handling implemented for async operations
- [ ] Loading states provided for all async UI
- [ ] File organization follows project structure
- [ ] Import aliases used instead of relative imports

### Performance Requirements
- [ ] Bundle size analysis shows no duplicate dependencies
- [ ] Component memoization used appropriately
- [ ] Images optimized with Next.js Image component
- [ ] Dynamic imports used for code splitting
- [ ] Core Web Vitals targets met

---

## 📊 Compliance Metrics

### Type Safety Score: 100%
- Zero `any` types in codebase
- Complete TypeScript coverage
- All props interfaces defined
- API responses typed

### Architecture Score: ≥90%
- Service layer adoption rate
- Context vs prop drilling ratio
- Component size (<300 lines)
- File organization compliance

### Performance Score: ≥85%
- Bundle size targets met
- Core Web Vitals passing
- Proper memoization usage
- Lazy loading implementation

### Code Quality Score: ≥95%
- ESLint error count: 0
- Test coverage: ≥80%
- Documentation coverage: ≥70%
- Build success rate: 100%

---

## 🏷️ Metadata
**Framework**: Next.js 13+ with App Router
**Language**: TypeScript (strict mode required)
**Architecture**: Service Layer + Context Pattern
**Quality**: Zero tolerance for violations
**AI-Friendly**: Optimized for LLM assistance

%%AI_HINT: These are NON-NEGOTIABLE requirements for Next.js development. Always enforce these patterns and immediately flag violations%%
