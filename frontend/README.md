# IKB Navigator Frontend

Modern Next.js frontend for the IKB Navigator AI-powered knowledge assistant.

## Features

- 🎨 Modern UI with Tailwind CSS + shadcn/ui
- 🌙 Dark mode support
- 📊 Real-time agent pipeline visualization
- 🔍 Google Drive document search
- 📄 Source preview with clickable links
- ⚡ Fast and responsive

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

### Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Architecture

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout with theme provider
│   ├── page.tsx           # Main page
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── ui/                # shadcn/ui components
│   ├── agent-timeline.tsx # Agent pipeline visualization
│   ├── chat-interface.tsx # Main chat UI
│   ├── source-preview.tsx # Document preview modal
│   ├── theme-provider.tsx # Theme context
│   └── theme-toggle.tsx   # Dark mode toggle
├── hooks/                 # Custom React hooks
│   └── useSearch.ts       # Search API hook
├── lib/                   # Utilities
│   ├── api.ts             # API client
│   └── utils.ts           # Helper functions
└── types/                 # TypeScript types
    └── index.ts           # Type definitions
```

## Key Components

### ChatInterface
Main component that handles search input, displays results, and coordinates all other components.

### AgentTimeline
Visualizes the agent pipeline showing:
- Query Understanding Agent
- Search Agent
- Analysis Agent
- Answer Generation Agent

Each agent shows:
- Current status (idle, running, completed, error)
- Execution time
- Progress indicators

### SourcePreview
Modal component that displays detailed information about a selected document source.

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Technology Stack

- **Next.js 15** - React framework
- **React 19** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components
- **Framer Motion** - Animations
- **Lucide React** - Icons
- **next-themes** - Dark mode

## API Integration

The frontend communicates with the FastAPI backend at `http://localhost:8000`:

- `POST /search` - Search documents
- `GET /health` - Health check
- `GET /agents/status` - Agent status
- `GET /graph/status` - LangGraph status

## Development

The application uses:
- Server Components for static content
- Client Components for interactivity
- TypeScript for type safety
- Tailwind for responsive design
- CSS variables for theming

## Production Build

```bash
# Build
npm run build

# Start production server
npm start
```

The application will be optimized for production with:
- Static generation where possible
- Optimized JavaScript bundles
- Image optimization
- CSS minification

## License

MIT
