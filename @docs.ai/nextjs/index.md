# ⚛️ Next.js Development Standards

## 🎯 Quick Summary
Universal development standards and patterns for Next.js applications with TypeScript. Designed for AI-assisted development and maintaining high code quality across projects.

## 📋 Table of Contents
1. [Critical Requirements](#critical-requirements)
2. [Architecture Patterns](#architecture-patterns)
3. [API Integration](#api-integration)
4. [Component Patterns](#component-patterns)
5. [Performance Guide](#performance-guide)
6. [Style Guide](#style-guide)

## 🔑 Key Standards at a Glance
- **TypeScript**: Strict mode, zero tolerance for `any` types
- **KISS Methodology**: Simple, clear, maintainable solutions
- **Data Preparation**: Transform data before render, not in JSX
- **Context Over Props**: Use React Context instead of prop drilling
- **Type Safety**: Generated types, proper error handling
- **Performance**: useMemo, useCallback, lazy loading

## 🚀 Quick Navigation

### 🚨 [CRITICAL_REQUIREMENTS.md](./CRITICAL_REQUIREMENTS.md) %%PRIORITY:HIGH%%
**Purpose**: Non-negotiable patterns and zero-tolerance violations for Next.js projects
**Use when**: Setting up project standards, code review guidelines
**Key sections**: Forbidden patterns, mandatory patterns, type safety rules
**Compliance**: Required for all Next.js projects

### 🔌 [API_PATTERNS.md](./API_PATTERNS.md) %%PRIORITY:HIGH%%
**Purpose**: Standardized API integration patterns for external services
**Use when**: Integrating APIs, setting up data fetching
**Key sections**: Service layer patterns, error handling, caching strategies
**Compliance**: Required for API integrations

### 🧩 [COMPONENT_PATTERNS.md](./COMPONENT_PATTERNS.md) %%PRIORITY:HIGH%%
**Purpose**: React component architecture and best practices
**Use when**: Building UI components, organizing component structure
**Key sections**: Component decomposition, context usage, state management
**Compliance**: Required for component development

### ⚡ [PERFORMANCE_GUIDE.md](./PERFORMANCE_GUIDE.md) %%PRIORITY:MEDIUM%%
**Purpose**: Performance optimization techniques for Next.js
**Use when**: Optimizing bundle size, improving page load speed
**Key sections**: Code splitting, memoization, bundle optimization
**Compliance**: Required for production applications

### 📝 [STYLE_GUIDE.md](./STYLE_GUIDE.md) %%PRIORITY:MEDIUM%%
**Purpose**: Code formatting, naming conventions, and project structure
**Use when**: Setting up new projects, maintaining consistency
**Key sections**: File organization, naming patterns, import structure
**Compliance**: Required for team consistency

### 🧪 [TESTING_STANDARDS.md](./TESTING_STANDARDS.md) %%PRIORITY:MEDIUM%%
**Purpose**: Testing patterns for Next.js applications
**Use when**: Writing tests for components, pages, and API routes
**Key sections**: Component testing, API testing, E2E testing
**Compliance**: Required for production applications

---

## 🎯 Implementation Levels

### 🟢 Level 1: Minimum Viable Standards (MUST HAVE)
**For every Next.js project**:
- [Critical Requirements](./CRITICAL_REQUIREMENTS.md) - Zero tolerance violations
- [API Patterns](./API_PATTERNS.md) - Basic service layer
- [Component Patterns](./COMPONENT_PATTERNS.md) - Component structure

### 🟡 Level 2: Production Ready (SHOULD HAVE)
**For production applications**:
- [Performance Guide](./PERFORMANCE_GUIDE.md) - Optimization techniques
- [Testing Standards](./TESTING_STANDARDS.md) - Comprehensive testing
- [Style Guide](./STYLE_GUIDE.md) - Team consistency

### 🔴 Level 3: Enterprise Ready (NICE TO HAVE)
**For large-scale applications**:
- Advanced patterns from all guides
- Custom tooling and automation
- Team-specific extensions

---

## 🛠 Core Technologies

### Required Stack
- **Next.js 13+**: App Router, Server Components
- **TypeScript 5+**: Strict mode enabled
- **React 18+**: Hooks, Context, Suspense
- **Tailwind CSS**: Utility-first styling

### Recommended Libraries
- **State Management**: Zustand, React Context
- **UI Components**: Radix UI, Headless UI
- **Forms**: React Hook Form, Zod validation
- **HTTP Client**: Fetch API, Axios
- **Testing**: Jest, React Testing Library, Playwright

### Development Tools
- **ESLint**: Code linting and standards
- **Prettier**: Code formatting
- **TypeScript**: Type checking
- **Husky**: Git hooks for quality gates

---

## 🚨 Universal Principles

### Zero Tolerance Violations
- **No `any` types** - Use proper TypeScript typing
- **No prop drilling** - Use Context for shared state
- **No data transformation in JSX** - Use useMemo pattern
- **No hardcoded values** - Use constants and configuration
- **No inline styles** - Use CSS classes or styled components

### Mandatory Patterns
- **Service layer** for all API calls
- **Error boundaries** for component error handling
- **Loading states** for all async operations
- **Type-safe** component props and API responses
- **Consistent file structure** and naming conventions

---

## 📊 Quality Metrics

### Code Quality Targets
- **TypeScript**: 100% typed, zero `any` usage
- **ESLint**: Zero errors, minimal warnings
- **Bundle Size**: <250KB initial load
- **Core Web Vitals**: LCP <2.5s, FID <100ms, CLS <0.1

### Performance Targets
- **First Contentful Paint**: <1.5s
- **Time to Interactive**: <3s
- **Bundle Analysis**: No duplicate dependencies
- **Image Optimization**: All images optimized

---

## 🔧 Quick Setup Commands

### Project Initialization
```bash
# Create Next.js project with TypeScript
npx create-next-app@latest project-name --typescript --tailwind --eslint --app

# Install recommended dependencies
npm install zustand react-hook-form zod @radix-ui/react-dialog

# Install development dependencies
npm install -D @types/node prettier husky lint-staged
```

### Quality Checks
```bash
# Type checking
npx tsc --noEmit

# Linting
npm run lint

# Build verification
npm run build

# Bundle analysis
npm run build && npx @next/bundle-analyzer
```

---

## 🏷️ Metadata
**Framework**: Next.js 13+ with App Router
**Language**: TypeScript (strict mode)
**Styling**: Tailwind CSS + Component Libraries
**Architecture**: Service Layer + Context Pattern
**Testing**: Jest + React Testing Library + Playwright
**Target**: Production-ready applications with AI-assisted development

%%AI_HINT: These standards ensure consistent, maintainable, and high-performance Next.js applications optimized for AI development assistance%%
