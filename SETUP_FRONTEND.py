"""
Frontend Foundation Generator for Lazarus Medical Dashboard
Creates all React + TypeScript files with proper directory structure
"""
import os
from pathlib import Path

BASE = Path(r"E:\Project Lazarus")

# Directory structure
DIRS = [
    "frontend",
    "frontend/src",
    "frontend/src/api",
    "frontend/src/components",
    "frontend/src/types",
    "frontend/src/styles",
    "frontend/public",
]

# File contents
FILES = {}

FILES["frontend/package.json"] = """{
  "name": "lazarus-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@tanstack/react-query": "^5.12.0",
    "recharts": "^2.10.0",
    "socket.io-client": "^4.6.0",
    "axios": "^1.6.2"
  },
  "devDependencies": {
    "@types/react": "^18.2.43",
    "@types/react-dom": "^18.2.17",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.7",
    "tailwindcss": "^3.3.6",
    "postcss": "^8.4.32",
    "autoprefixer": "^10.4.16",
    "vitest": "^1.0.4"
  }
}
"""

FILES["frontend/vite.config.ts"] = """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
});
"""

FILES["frontend/tsconfig.json"] = """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
"""

FILES["frontend/tsconfig.node.json"] = """{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
"""

FILES["frontend/tailwind.config.js"] = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        clinical: {
          bg: '#0a0e14',
          surface: '#1a1f2e',
          border: '#2d3748',
          text: '#e2e8f0',
          'text-muted': '#94a3b8',
          critical: '#ef4444',
          warning: '#f59e0b',
          normal: '#10b981',
          info: '#3b82f6',
          accent: '#8b5cf6',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Consolas', 'Monaco', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'clinical': '0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -1px rgba(0, 0, 0, 0.3)',
        'clinical-lg': '0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -2px rgba(0, 0, 0, 0.3)',
      },
    },
  },
  plugins: [],
}
"""

FILES["frontend/postcss.config.js"] = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""

FILES["frontend/index.html"] = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Lazarus Medical Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""

FILES["frontend/src/main.tsx"] = """import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import './styles/index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30000,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
);
"""

FILES["frontend/src/App.tsx"] = """import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import PatientDetail from './components/PatientDetail';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-clinical-bg text-clinical-text">
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/patient/:id" element={<PatientDetail />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
"""

FILES["frontend/src/api/client.ts"] = """import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export default apiClient;
"""

FILES["frontend/src/api/websocket.ts"] = """import { io, Socket } from 'socket.io-client';

class WebSocketClient {
  private socket: Socket | null = null;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();

  connect() {
    if (this.socket?.connected) return;

    this.socket = io('ws://localhost:8000', {
      transports: ['websocket'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    this.socket.on('vitals_update', (data) => {
      this.emit('vitals_update', data);
    });

    this.socket.on('alert', (data) => {
      this.emit('alert', data);
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  on(event: string, callback: (data: any) => void) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  off(event: string, callback: (data: any) => void) {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.delete(callback);
    }
  }

  private emit(event: string, data: any) {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.forEach(callback => callback(data));
    }
  }

  subscribeToPatient(patientId: string) {
    if (this.socket) {
      this.socket.emit('subscribe_patient', { patient_id: patientId });
    }
  }

  unsubscribeFromPatient(patientId: string) {
    if (this.socket) {
      this.socket.emit('unsubscribe_patient', { patient_id: patientId });
    }
  }
}

export const wsClient = new WebSocketClient();
"""

FILES["frontend/src/types/index.ts"] = """export interface Patient {
  id: string;
  name: string;
  age: number;
  gender: string;
  admission_date: string;
  diagnosis: string;
  room: string;
  status: 'stable' | 'critical' | 'recovering';
}

export interface Vitals {
  id: string;
  patient_id: string;
  timestamp: string;
  heart_rate: number;
  blood_pressure_systolic: number;
  blood_pressure_diastolic: number;
  oxygen_saturation: number;
  temperature: number;
  respiratory_rate: number;
}

export interface Alert {
  id: string;
  patient_id: string;
  type: 'critical' | 'warning' | 'info';
  message: string;
  timestamp: string;
  acknowledged: boolean;
}

export interface Prescription {
  id: string;
  patient_id: string;
  medication: string;
  dosage: string;
  frequency: string;
  start_date: string;
  end_date?: string;
  status: 'active' | 'completed' | 'discontinued';
}

export interface VitalsHistory {
  timestamps: string[];
  heart_rate: number[];
  blood_pressure_systolic: number[];
  blood_pressure_diastolic: number[];
  oxygen_saturation: number[];
  temperature: number[];
  respiratory_rate: number[];
}
"""

FILES["frontend/src/styles/index.css"] = """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-clinical-bg text-clinical-text font-sans antialiased;
  }

  * {
    @apply border-clinical-border;
  }
}

@layer components {
  .card {
    @apply bg-clinical-surface rounded-lg p-6 shadow-clinical border border-clinical-border;
  }

  .card-header {
    @apply text-xl font-semibold mb-4 text-clinical-text;
  }

  .vital-value {
    @apply font-mono text-2xl font-bold;
  }

  .vital-label {
    @apply text-sm text-clinical-text-muted uppercase tracking-wide;
  }

  .alert-critical {
    @apply bg-clinical-critical/10 border-clinical-critical text-clinical-critical;
  }

  .alert-warning {
    @apply bg-clinical-warning/10 border-clinical-warning text-clinical-warning;
  }

  .alert-info {
    @apply bg-clinical-info/10 border-clinical-info text-clinical-info;
  }

  .status-critical {
    @apply text-clinical-critical;
  }

  .status-warning {
    @apply text-clinical-warning;
  }

  .status-normal {
    @apply text-clinical-normal;
  }

  .btn {
    @apply px-4 py-2 rounded-md font-medium transition-colors duration-200;
  }

  .btn-primary {
    @apply bg-clinical-accent hover:bg-clinical-accent/80 text-white;
  }

  .btn-secondary {
    @apply bg-clinical-surface hover:bg-clinical-border text-clinical-text border border-clinical-border;
  }

  .input {
    @apply bg-clinical-surface border border-clinical-border rounded-md px-3 py-2 text-clinical-text placeholder-clinical-text-muted focus:outline-none focus:ring-2 focus:ring-clinical-accent;
  }

  .data-grid {
    @apply grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3;
  }

  .metric-card {
    @apply card p-4;
  }

  .metric-value {
    @apply vital-value;
  }

  .metric-label {
    @apply vital-label;
  }

  .chart-container {
    @apply w-full h-64 mt-4;
  }
}

@layer utilities {
  .clinical-divider {
    @apply border-t border-clinical-border my-4;
  }

  .clinical-scrollbar::-webkit-scrollbar {
    width: 8px;
  }

  .clinical-scrollbar::-webkit-scrollbar-track {
    @apply bg-clinical-surface;
  }

  .clinical-scrollbar::-webkit-scrollbar-thumb {
    @apply bg-clinical-border rounded-full;
  }

  .clinical-scrollbar::-webkit-scrollbar-thumb:hover {
    @apply bg-clinical-text-muted;
  }
}
"""

FILES["frontend/src/components/Dashboard.tsx"] = """// Placeholder component - will be implemented in next phase
export default function Dashboard() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">Lazarus Medical Dashboard</h1>
      <p className="text-clinical-text-muted">Dashboard component placeholder - ready for implementation</p>
    </div>
  );
}
"""

FILES["frontend/src/components/PatientDetail.tsx"] = """// Placeholder component - will be implemented in next phase
export default function PatientDetail() {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-4">Patient Details</h1>
      <p className="text-clinical-text-muted">Patient detail component placeholder - ready for implementation</p>
    </div>
  );
}
"""

def main():
    print("🏗️  Creating Lazarus Frontend Foundation...")
    print()
    
    # Create directories
    print("📁 Creating directories...")
    for dir_path in DIRS:
        full_path = BASE / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"   ✓ {dir_path}")
    print()
    
    # Create files
    print("📝 Creating files...")
    for file_path, content in FILES.items():
        full_path = BASE / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')
        print(f"   ✓ {file_path}")
    print()
    
    print("✅ Frontend Foundation Complete!")
    print()
    print(f"📦 Created {len(DIRS)} directories")
    print(f"📄 Created {len(FILES)} files")
    print()
    print("🚀 Next steps:")
    print("   1. cd frontend")
    print("   2. npm install")
    print("   3. npm run dev")

if __name__ == "__main__":
    main()
