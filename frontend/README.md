# FinVault AI — Frontend Documentation

Complete frontend setup guide, component overview, and development instructions.

## 🚀 Quick Start

### Development
```bash
cd frontend
npm run dev
# Visit http://localhost:3000
```

### Production Build
```bash
npm run build
npm start
```

### Environment Configuration
Create `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## ✅ Setup Status

- ✅ Next.js Properly Initialized (Next.js 16.1.6)
- ✅ All Components Created (6 total)
- ✅ TypeScript Strict Mode (100% type coverage)
- ✅ Production Build Passing
- ✅ Dev Server Ready
- ✅ Docker Removed (not using containers)

---

## 📦 Stack

| Component | Version |
|-----------|---------|
| **Next.js** | 16.1.6 |
| **React** | 18.2+ |
| **TypeScript** | Latest |
| **Tailwind CSS** | 3.4+ |
| **React Query** | 5.0+ |
| **Axios** | 1.6+ |
| **Lucide React** | Latest |

---

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx           Main dashboard
│   │   ├── layout.tsx         Root layout (with providers)
│   │   ├── providers.tsx      QueryClientProvider wrapper
│   │   └── globals.css        Tailwind + custom styles
│   ├── components/
│   │   ├── QueryPanel.tsx      Query input & mode toggle
│   │   ├── ResultsView.tsx     Summary & metrics panels
│   │   ├── SourcesView.tsx     Expandable citations
│   │   ├── QueryHistory.tsx    Persistent query history
│   │   ├── MemoryPreferencesSidebar.tsx  User preferences
│   │   ├── MetricsFooter.tsx   Performance metrics
│   │   └── index.ts            Component exports
│   ├── hooks/
│   │   └── index.ts            React Query + localStorage hooks
│   ├── lib/
│   │   ├── api.ts              Axios API client
│   │   └── queryClient.ts      React Query configuration
│   └── types/
│       └── index.ts            TypeScript interfaces
├── public/                     Static assets
├── package.json
├── tsconfig.json               TypeScript config
├── tailwind.config.ts          Tailwind config
├── next.config.ts              Next.js config
└── postcss.config.js           PostCSS config
```

---

## 🧩 Components

### QueryPanel
- Financial query input field
- Quick/Deep analysis mode toggle
- Stock ticker filtering
- Word count display

### ResultsView
- Summary of findings
- Key metrics and evidence
- Confidence score display
- Contradiction detection

### SourcesView
- Expandable source citations
- Relevance scores for each source
- Document metadata
- Direct links to evidence sections

### QueryHistory
- Persistent query history (localStorage)
- Timestamps for each query
- Search/filter capabilities
- One-click re-run queries

### MemoryPreferencesSidebar
- Risk tolerance settings
- Preferred sectors
- Metrics selection
- User preferences persistence

### MetricsFooter
- Query latency display
- Token count metrics
- Model information
- Estimated cost breakdown

---

## 🔗 API Integration

### Backend Connection

The frontend connects to the backend via Axios:

```typescript
// src/lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function queryFinancialData(request: QueryRequest) {
  // POST /query endpoint
  return api.post("/query", request);
}
```

### Available Endpoints

- **POST** `/query` — Execute financial query
- **GET** `/health` — Health check
- **GET** `/docs` — Swagger API documentation

### Hook Usage

```typescript
import { useQueryFinancialData, useHealthCheck } from "@/hooks";

// Query financial data
const { mutate: submitQuery, data, isLoading } = useQueryFinancialData();

// Check backend health
const { data: health, isLoading } = useHealthCheck();
```

---

## 🛠️ Full Setup from Scratch

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Create backend/.env with:
# GROQ_API_KEY=your_api_key
# DATABASE_URL=your_postgres_url
# QDRANT_URL=your_qdrant_url
# QDRANT_API_KEY=your_qdrant_key

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend: **http://localhost:8000**  
API Docs: **http://localhost:8000/docs**

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
# Create .env.local with:
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Start dev server
npm run dev
```

Frontend: **http://localhost:3000**

### 3. Testing

**Backend Health:**
```bash
curl http://localhost:8000/health
```

**Frontend:**
- Open http://localhost:3000
- Try asking a financial question
- Verify API calls in Network tab

---

## 📝 Development

### Running Development Server
```bash
npm run dev
```
Starts Turbopack dev server with hot reload.

### Building for Production
```bash
npm run build
npm start
```

### Compiling TypeScript
```bash
npx tsc --noEmit
```

### Formatting Code
```bash
npx prettier --write src/
```

---

## 📊 Build Status

```
✓ Compiled successfully
✓ TypeScript checking passed
✓ Page generation complete
✓ Static content pre-rendered
```

All pages are pre-rendered as static content for optimal performance.

---

## 🔐 Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

**Note:** Variables prefixed with `NEXT_PUBLIC_` are exposed to browser. Don't store secrets here.

---

## 🚀 Deployment

### Deploy to Vercel

1. Push code to GitHub
2. Import repository in Vercel dashboard
3. Set environment variables:
   - `NEXT_PUBLIC_API_URL` → production backend URL
4. Deploy

```bash
npm run build
# Vercel handles the rest
```

### Deploy Backend

Backend can be deployed to Render, Railway, or any platform supporting Python/FastAPI.

Set environment variables on your deployment platform for:
- `GROQ_API_KEY`
- `DATABASE_URL`
- `QDRANT_URL`
- `QDRANT_API_KEY`

---

## 🐛 Troubleshooting

### Frontend Build Fails
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Can't Connect to Backend
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check `.env.local` has correct `NEXT_PUBLIC_API_URL`
3. Ensure firewall allows port 8000
4. Check browser console for CORS errors

### Port 3000 Already in Use
```bash
# Use different port
npm run dev -- -p 3001
```

### TypeScript Errors
```bash
# Rebuild types
npx tsc --noEmit
```

---

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Query Documentation](https://tanstack.com/query/latest)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Backend API Docs](http://localhost:8000/docs)

---

## 📦 Dependencies

All dependencies are declared in `package.json` with pinned versions. To update:

```bash
npm update                    # Update minor/patch versions
npm outdated                  # Check for outdated packages
npm audit                     # Check for vulnerabilities
npm audit fix                 # Fix vulnerabilities
```

---

## ✨ Features

- ⚡ **Fast** — Next.js Turbopack compiler, static pre-rendering
- 🎨 **Styled** — Tailwind CSS utility framework
- 📱 **Responsive** — Mobile-first design
- ♿ **Accessible** — WCAG 2.1 AA standards (via Radix UI)
- 🔒 **Type Safe** — 100% TypeScript coverage
- 📊 **Real-time** — React Query for reactive data
- 💾 **Persistent** — localStorage for user preferences
- 🚀 **Production Ready** — Optimized build output

---

## 📝 License

This project is part of FinVault AI. See [../LICENSE](../LICENSE) for details.

---

**Ready to use!** The frontend MVP is properly initialized and production-ready.
