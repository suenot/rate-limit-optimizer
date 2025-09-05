# ⚡ Next.js Performance Guide %%PRIORITY:MEDIUM%%

## 🎯 Quick Summary
Performance optimization techniques for Next.js applications including bundle optimization, image handling, caching strategies, and Core Web Vitals improvement.

## 📋 Table of Contents
1. [Bundle Optimization](#bundle-optimization)
2. [Image Optimization](#image-optimization)
3. [Caching Strategies](#caching-strategies)
4. [Core Web Vitals](#core-web-vitals)
5. [Monitoring & Analytics](#monitoring--analytics)
6. [Performance Budget](#performance-budget)

## 🔑 Key Metrics at a Glance
- **LCP**: <2.5s (Largest Contentful Paint)
- **FID**: <100ms (First Input Delay)
- **CLS**: <0.1 (Cumulative Layout Shift)
- **Bundle Size**: <250KB initial load
- **Image Optimization**: WebP/AVIF with proper sizing
- **Caching**: Strategic use of ISR and client-side caching

---

## 📦 Bundle Optimization

### Dynamic Imports and Code Splitting

#### Page-Level Code Splitting
```typescript
// pages/dashboard.tsx - Automatically code-split
import dynamic from 'next/dynamic';
import { Suspense } from 'react';

// Lazy load heavy components
const DashboardCharts = dynamic(() => import('@/components/DashboardCharts'), {
  loading: () => <ChartsSkeleton />,
  ssr: false, // Client-side only for chart libraries
});

const UserManagement = dynamic(() => import('@/components/UserManagement'), {
  loading: () => <div>Loading users...</div>,
});

// Component-level lazy loading
const HeavyModal = dynamic(() => import('@/components/HeavyModal'));

export default function Dashboard() {
  const [showModal, setShowModal] = useState(false);

  return (
    <div>
      <Suspense fallback={<DashboardSkeleton />}>
        <DashboardCharts />
      </Suspense>

      <UserManagement />

      {showModal && (
        <Suspense fallback={<ModalSkeleton />}>
          <HeavyModal onClose={() => setShowModal(false)} />
        </Suspense>
      )}
    </div>
  );
}
```

#### Library Code Splitting
```typescript
// utils/chartHelpers.ts - Split chart utilities
export const loadChartingLibrary = async () => {
  const [
    { Chart },
    { CategoryScale, LinearScale, PointElement, LineElement }
  ] = await Promise.all([
    import('chart.js'),
    import('chart.js/auto')
  ]);

  // Register only needed components
  Chart.register(CategoryScale, LinearScale, PointElement, LineElement);

  return Chart;
};

// components/Chart.tsx
function Chart({ data }: ChartProps) {
  const [chartLib, setChartLib] = useState<any>(null);

  useEffect(() => {
    loadChartingLibrary().then(setChartLib);
  }, []);

  if (!chartLib) {
    return <ChartSkeleton />;
  }

  return <canvas ref={chartRef} />;
}
```

#### Bundle Analysis Configuration
```javascript
// next.config.js
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

module.exports = withBundleAnalyzer({
  // Enable experimental features
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ['lucide-react', '@radix-ui/react-icons'],
  },

  // Webpack optimizations
  webpack: (config, { dev, isServer }) => {
    // Production optimizations
    if (!dev && !isServer) {
      config.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            chunks: 'all',
          },
          common: {
            name: 'common',
            minChunks: 2,
            chunks: 'all',
          },
        },
      };
    }

    return config;
  },
});

// package.json scripts
{
  "analyze": "ANALYZE=true npm run build",
  "analyze:server": "BUNDLE_ANALYZE=server npm run build",
  "analyze:browser": "BUNDLE_ANALYZE=browser npm run build"
}
```

### Tree Shaking and Dead Code Elimination

#### Optimize Library Imports
```typescript
// ❌ BAD - Imports entire library
import * as _ from 'lodash';
import { format } from 'date-fns';

// ✅ GOOD - Import only what you need
import { debounce, throttle } from 'lodash-es';
import { format } from 'date-fns/format';
import { parseISO } from 'date-fns/parseISO';

// ✅ BETTER - Use modular alternatives
import debounce from 'lodash.debounce';
import throttle from 'lodash.throttle';

// Custom utility for simple cases
export function formatCurrency(amount: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(amount);
}
```

#### Conditional Imports
```typescript
// utils/conditionalImports.ts
export const loadDevTools = async () => {
  if (process.env.NODE_ENV === 'development') {
    const { default: devtools } = await import('@/utils/devtools');
    return devtools;
  }
  return null;
};

// Conditional polyfills
export const loadPolyfills = async () => {
  const promises = [];

  if (!('IntersectionObserver' in window)) {
    promises.push(import('intersection-observer'));
  }

  if (!('ResizeObserver' in window)) {
    promises.push(import('resize-observer-polyfill'));
  }

  await Promise.all(promises);
};
```

---

## 🖼️ Image Optimization

### Next.js Image Component

#### Responsive Images with Sizing
```typescript
import Image from 'next/image';

// ✅ GOOD - Responsive image with proper sizing
function ProductCard({ product }: { product: Product }) {
  return (
    <div className="relative">
      <Image
        src={product.imageUrl}
        alt={product.name}
        width={300}
        height={200}
        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
        style={{
          objectFit: 'cover',
          width: '100%',
          height: 'auto',
        }}
        priority={product.featured} // Load important images first
        placeholder="blur"
        blurDataURL="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQ..." // Low-res placeholder
      />
    </div>
  );
}

// Dynamic image sizing
function ResponsiveImage({ src, alt }: { src: string; alt: string }) {
  return (
    <div className="relative w-full h-64">
      <Image
        src={src}
        alt={alt}
        fill
        sizes="(max-width: 768px) 100vw, 50vw"
        style={{ objectFit: 'cover' }}
        className="rounded-lg"
      />
    </div>
  );
}
```

#### Advanced Image Optimization
```typescript
// utils/imageOptimization.ts
export interface ImageOptions {
  width?: number;
  height?: number;
  quality?: number;
  format?: 'webp' | 'avif' | 'auto';
}

export function getOptimizedImageUrl(
  src: string,
  options: ImageOptions = {}
): string {
  const { width, height, quality = 75, format = 'auto' } = options;

  const params = new URLSearchParams();
  if (width) params.set('w', width.toString());
  if (height) params.set('h', height.toString());
  params.set('q', quality.toString());
  params.set('f', format);

  return `/_next/image?url=${encodeURIComponent(src)}&${params.toString()}`;
}

// Image with srcSet for different densities
function HighDPIImage({ src, alt, width, height }: ImageProps) {
  const srcSet = [
    `${getOptimizedImageUrl(src, { width, height })} 1x`,
    `${getOptimizedImageUrl(src, { width: width * 2, height: height * 2 })} 2x`,
    `${getOptimizedImageUrl(src, { width: width * 3, height: height * 3 })} 3x`,
  ].join(', ');

  return (
    <img
      src={getOptimizedImageUrl(src, { width, height })}
      srcSet={srcSet}
      alt={alt}
      width={width}
      height={height}
      loading="lazy"
    />
  );
}
```

### Image Loading Strategies

#### Progressive Loading with Intersection Observer
```typescript
// hooks/useIntersectionObserver.ts
export function useIntersectionObserver(
  ref: RefObject<Element>,
  options: IntersectionObserverInit = {}
): boolean {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      {
        threshold: 0.1,
        rootMargin: '50px',
        ...options,
      }
    );

    observer.observe(element);

    return () => observer.disconnect();
  }, [ref, options]);

  return isVisible;
}

// components/LazyImage.tsx
function LazyImage({ src, alt, ...props }: ImageProps) {
  const imageRef = useRef<HTMLDivElement>(null);
  const isVisible = useIntersectionObserver(imageRef);
  const [loaded, setLoaded] = useState(false);

  return (
    <div ref={imageRef} className="relative overflow-hidden">
      {isVisible && (
        <Image
          src={src}
          alt={alt}
          onLoad={() => setLoaded(true)}
          className={cn(
            'transition-opacity duration-300',
            loaded ? 'opacity-100' : 'opacity-0'
          )}
          {...props}
        />
      )}

      {!loaded && (
        <div className="absolute inset-0 bg-gray-200 animate-pulse" />
      )}
    </div>
  );
}
```

---

## 💾 Caching Strategies

### Next.js Caching Layers

#### ISR (Incremental Static Regeneration)
```typescript
// pages/products/[id].tsx
interface ProductPageProps {
  product: Product;
  relatedProducts: Product[];
}

export default function ProductPage({ product, relatedProducts }: ProductPageProps) {
  return (
    <div>
      <ProductDetails product={product} />
      <RelatedProducts products={relatedProducts} />
    </div>
  );
}

export async function getStaticPaths() {
  // Pre-build most popular products
  const popularProducts = await ProductService.getPopularProducts();

  const paths = popularProducts.map(product => ({
    params: { id: product.id },
  }));

  return {
    paths,
    fallback: 'blocking', // Generate other pages on-demand
  };
}

export async function getStaticProps({ params }: GetStaticPropsContext) {
  try {
    const [product, relatedProducts] = await Promise.all([
      ProductService.getProduct(params!.id as string),
      ProductService.getRelatedProducts(params!.id as string),
    ]);

    return {
      props: {
        product,
        relatedProducts,
      },
      revalidate: 3600, // Revalidate every hour
    };
  } catch (error) {
    return {
      notFound: true,
    };
  }
}
```

#### App Router Caching
```typescript
// app/products/[id]/page.tsx
async function getProduct(id: string) {
  const res = await fetch(`${API_URL}/products/${id}`, {
    next: {
      revalidate: 3600, // Cache for 1 hour
      tags: ['product', `product-${id}`]
    },
  });

  if (!res.ok) {
    throw new Error('Failed to fetch product');
  }

  return res.json();
}

async function getRelatedProducts(id: string) {
  const res = await fetch(`${API_URL}/products/${id}/related`, {
    next: {
      revalidate: 7200, // Cache for 2 hours
      tags: ['products', 'related']
    },
  });

  return res.json();
}

export default async function ProductPage({ params }: { params: { id: string } }) {
  const [product, relatedProducts] = await Promise.all([
    getProduct(params.id),
    getRelatedProducts(params.id),
  ]);

  return (
    <div>
      <ProductDetails product={product} />
      <RelatedProducts products={relatedProducts} />
    </div>
  );
}

// Revalidate cache when product updates
export async function revalidateProduct(productId: string) {
  revalidateTag(`product-${productId}`);
  revalidateTag('products');
}
```

### Client-Side Caching

#### SWR with Advanced Caching
```typescript
// lib/swrConfig.ts
import { SWRConfig } from 'swr';

const swrConfig = {
  refreshInterval: 0,
  revalidateOnFocus: false,
  revalidateOnReconnect: true,
  dedupingInterval: 5000,
  errorRetryCount: 3,
  errorRetryInterval: 5000,

  // Cache provider for persistent caching
  provider: () => {
    const map = new Map();

    // Load from localStorage on initialization
    if (typeof window !== 'undefined') {
      try {
        const cached = localStorage.getItem('swr-cache');
        if (cached) {
          const parsedCache = JSON.parse(cached);
          Object.entries(parsedCache).forEach(([key, value]) => {
            map.set(key, value);
          });
        }
      } catch (error) {
        console.warn('Failed to load SWR cache from localStorage');
      }
    }

    return map;
  },

  // Save to localStorage periodically
  onSuccess: (data, key) => {
    if (typeof window !== 'undefined') {
      try {
        const cache = {};
        map.forEach((value, key) => {
          cache[key] = value;
        });
        localStorage.setItem('swr-cache', JSON.stringify(cache));
      } catch (error) {
        console.warn('Failed to save SWR cache to localStorage');
      }
    }
  },
};

export function SWRProvider({ children }: { children: ReactNode }) {
  return <SWRConfig value={swrConfig}>{children}</SWRConfig>;
}
```

#### React Query with Persistence
```typescript
// lib/queryClient.ts
import { QueryClient, QueryCache } from '@tanstack/react-query';
import { persistQueryClient } from '@tanstack/react-query-persist-client-core';
import { createSyncStoragePersister } from '@tanstack/query-sync-storage-persister';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error) => {
        if (error.status === 404) return false;
        return failureCount < 3;
      },
    },
  },
  queryCache: new QueryCache({
    onError: (error) => {
      console.error('Query error:', error);
      // Send to error reporting
    },
  }),
});

// Persist to localStorage
if (typeof window !== 'undefined') {
  const persister = createSyncStoragePersister({
    storage: window.localStorage,
    key: 'react-query-cache',
  });

  persistQueryClient({
    queryClient,
    persister,
    maxAge: 24 * 60 * 60 * 1000, // 24 hours
  });
}

export { queryClient };
```

---

## 📊 Core Web Vitals

### Largest Contentful Paint (LCP) Optimization

#### Critical Resource Preloading
```typescript
// components/CriticalResourcePreloader.tsx
export function CriticalResourcePreloader() {
  return (
    <Head>
      {/* Preload critical fonts */}
      <link
        rel="preload"
        href="/fonts/inter-var.woff2"
        as="font"
        type="font/woff2"
        crossOrigin="anonymous"
      />

      {/* Preload critical images */}
      <link
        rel="preload"
        href="/images/hero-image.webp"
        as="image"
        type="image/webp"
      />

      {/* Preload critical API data */}
      <link
        rel="preload"
        href="/api/critical-data"
        as="fetch"
        crossOrigin="anonymous"
      />

      {/* DNS prefetch for external domains */}
      <link rel="dns-prefetch" href="//fonts.googleapis.com" />
      <link rel="dns-prefetch" href="//api.example.com" />

      {/* Preconnect to critical third-party origins */}
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
    </Head>
  );
}
```

#### Above-the-Fold Optimization
```typescript
// components/HeroSection.tsx
function HeroSection() {
  return (
    <section className="relative h-screen flex items-center">
      {/* Critical image with priority loading */}
      <Image
        src="/images/hero-image.webp"
        alt="Hero image"
        fill
        style={{ objectFit: 'cover' }}
        priority
        sizes="100vw"
        className="absolute inset-0 z-0"
      />

      {/* Critical content that should be visible immediately */}
      <div className="relative z-10 container mx-auto">
        <h1 className="text-4xl md:text-6xl font-bold text-white">
          Welcome to Our Platform
        </h1>
        <p className="text-xl text-white mt-4">
          Discover amazing features and capabilities
        </p>
        <Button className="mt-8" size="lg">
          Get Started
        </Button>
      </div>
    </section>
  );
}
```

### Cumulative Layout Shift (CLS) Prevention

#### Skeleton Loading Patterns
```typescript
// components/skeletons/UserListSkeleton.tsx
export function UserListSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="border rounded-lg p-4">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-gray-200 rounded-full animate-pulse" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-gray-200 rounded w-3/4 animate-pulse" />
              <div className="h-3 bg-gray-200 rounded w-1/2 animate-pulse" />
            </div>
            <div className="w-20 h-8 bg-gray-200 rounded animate-pulse" />
          </div>
        </div>
      ))}
    </div>
  );
}

// Usage with proper dimensions
function UserList() {
  const { users, loading } = useUsers();

  if (loading) {
    return (
      <div className="min-h-[400px]"> {/* Reserve space to prevent CLS */}
        <UserListSkeleton />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {users.map(user => (
        <UserCard key={user.id} user={user} />
      ))}
    </div>
  );
}
```

#### Fixed Dimensions for Dynamic Content
```typescript
// components/DynamicImageCard.tsx
function DynamicImageCard({ src, title, description }: CardProps) {
  const [imageLoaded, setImageLoaded] = useState(false);

  return (
    <div className="border rounded-lg overflow-hidden">
      {/* Fixed aspect ratio container */}
      <div className="relative w-full" style={{ aspectRatio: '16/9' }}>
        <Image
          src={src}
          alt={title}
          fill
          style={{ objectFit: 'cover' }}
          onLoad={() => setImageLoaded(true)}
          className={cn(
            'transition-opacity duration-300',
            imageLoaded ? 'opacity-100' : 'opacity-0'
          )}
        />
        {!imageLoaded && (
          <div className="absolute inset-0 bg-gray-200 animate-pulse" />
        )}
      </div>

      {/* Fixed height for text content */}
      <div className="p-4 h-32 flex flex-col justify-between">
        <h3 className="font-semibold text-lg line-clamp-2">{title}</h3>
        <p className="text-gray-600 text-sm line-clamp-3">{description}</p>
      </div>
    </div>
  );
}
```

---

## 📈 Monitoring & Analytics

### Performance Monitoring Setup

#### Core Web Vitals Tracking
```typescript
// lib/webVitals.ts
import { getCLS, getFCP, getFID, getLCP, getTTFB } from 'web-vitals';

interface PerformanceMetric {
  name: string;
  value: number;
  id: string;
  delta: number;
  navigationType: string;
}

function sendToAnalytics(metric: PerformanceMetric) {
  // Send to your analytics service
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', metric.name, {
      value: Math.round(metric.value),
      event_category: 'Web Vitals',
      event_label: metric.id,
      non_interaction: true,
    });
  }

  // Send to custom analytics
  fetch('/api/analytics', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      metric: metric.name,
      value: metric.value,
      page: window.location.pathname,
      timestamp: Date.now(),
    }),
  }).catch(console.error);
}

// Measure all Core Web Vitals
export function measureWebVitals() {
  getCLS(sendToAnalytics);
  getFCP(sendToAnalytics);
  getFID(sendToAnalytics);
  getLCP(sendToAnalytics);
  getTTFB(sendToAnalytics);
}

// pages/_app.tsx
export function reportWebVitals(metric: any) {
  sendToAnalytics(metric);
}
```

#### Performance Budget Monitoring
```typescript
// lib/performanceBudget.ts
interface PerformanceBudget {
  lcp: number; // ms
  fid: number; // ms
  cls: number; // score
  bundleSize: number; // KB
  imageSize: number; // KB
}

const PERFORMANCE_BUDGET: PerformanceBudget = {
  lcp: 2500,
  fid: 100,
  cls: 0.1,
  bundleSize: 250,
  imageSize: 500,
};

export function checkPerformanceBudget(metrics: Partial<PerformanceBudget>) {
  const violations = [];

  Object.entries(metrics).forEach(([key, value]) => {
    const budget = PERFORMANCE_BUDGET[key as keyof PerformanceBudget];
    if (value > budget) {
      violations.push({
        metric: key,
        value,
        budget,
        overage: value - budget,
      });
    }
  });

  if (violations.length > 0) {
    console.warn('Performance budget violations:', violations);

    // Send alert to monitoring service
    fetch('/api/performance-alerts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ violations }),
    }).catch(console.error);
  }

  return violations;
}
```

### Continuous Performance Monitoring

#### Lighthouse CI Integration
```yaml
# .github/workflows/lighthouse-ci.yml
name: Lighthouse CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Build application
        run: npm run build

      - name: Run Lighthouse CI
        run: |
          npm install -g @lhci/cli@0.12.x
          lhci autorun
        env:
          LHCI_GITHUB_APP_TOKEN: ${{ secrets.LHCI_GITHUB_APP_TOKEN }}
```

```javascript
// lighthouserc.js
module.exports = {
  ci: {
    collect: {
      url: [
        'http://localhost:3000',
        'http://localhost:3000/dashboard',
        'http://localhost:3000/products',
      ],
      startServerCommand: 'npm start',
      numberOfRuns: 3,
    },
    assert: {
      assertions: {
        'categories:performance': ['error', { minScore: 0.9 }],
        'categories:accessibility': ['error', { minScore: 0.9 }],
        'categories:best-practices': ['error', { minScore: 0.9 }],
        'categories:seo': ['error', { minScore: 0.9 }],
        'first-contentful-paint': ['error', { maxNumericValue: 2000 }],
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        'total-blocking-time': ['error', { maxNumericValue: 300 }],
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
  },
};
```

---

## 💰 Performance Budget

### Bundle Size Limits
```json
{
  "budgets": [
    {
      "type": "initial",
      "maximumWarning": "200kb",
      "maximumError": "250kb"
    },
    {
      "type": "anyComponentStyle",
      "maximumWarning": "5kb",
      "maximumError": "10kb"
    },
    {
      "type": "bundle",
      "name": "vendor",
      "maximumWarning": "150kb",
      "maximumError": "200kb"
    }
  ]
}
```

### Performance Checklist

#### Pre-Deployment Checklist
- [ ] **Bundle Analysis**: Analyzed bundle size and dependencies
- [ ] **Image Optimization**: All images optimized and properly sized
- [ ] **Critical Resource Preloading**: Critical fonts, images, and data preloaded
- [ ] **Code Splitting**: Dynamic imports used for heavy components
- [ ] **Caching Strategy**: Appropriate cache headers and ISR configured
- [ ] **Core Web Vitals**: LCP < 2.5s, FID < 100ms, CLS < 0.1
- [ ] **Lighthouse Score**: Performance score > 90
- [ ] **Performance Budget**: No budget violations detected

#### Monitoring Setup
- [ ] **Web Vitals Tracking**: Real user metrics collected
- [ ] **Error Tracking**: Performance errors monitored
- [ ] **Lighthouse CI**: Automated performance testing
- [ ] **Bundle Size Monitoring**: Bundle size tracked over time
- [ ] **Performance Alerts**: Alerts configured for regressions

---

## 🏷️ Metadata
**Framework**: Next.js 13+ with App Router
**Focus**: Bundle optimization, Core Web Vitals, caching
**Tools**: Lighthouse, Bundle Analyzer, Web Vitals
**Targets**: LCP <2.5s, FID <100ms, CLS <0.1, Bundle <250KB
**Monitoring**: Real user metrics, CI/CD integration

%%AI_HINT: These performance optimizations are essential for production Next.js applications and should be implemented progressively based on application needs%%
