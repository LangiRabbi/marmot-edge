# Marmot Industrial Dashboard

Futuristic edge processing system for monitoring production workstations.

## Technology Stack

- **Vite** - Build tool
- **TypeScript** - Type-safe JavaScript
- **React** - UI framework
- **shadcn/ui** - Component library
- **Tailwind CSS** - Styling

## Development

### Prerequisites
- Node.js (recommended via [nvm](https://github.com/nvm-sh/nvm))
- npm or bun

### Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

The development server runs on `http://localhost:8080`

## Project Structure

```
src/
├── components/     # Reusable UI components
├── hooks/         # Custom React hooks
├── lib/           # Utility functions
├── pages/         # Application pages/routes
├── App.tsx        # Main application component
└── main.tsx       # Application entry point
```