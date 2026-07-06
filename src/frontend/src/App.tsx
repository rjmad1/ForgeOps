import { useState, useEffect } from 'react';
import { 
  Home, Server, Layers, ShieldCheck, Cpu, Terminal, Settings, 
  Sun, Moon, AlertOctagon, Radio, HelpCircle, Activity
} from 'lucide-react';
import HomeView from './components/HomeView';
import ServicesView from './components/ServicesView';
import ModelsView from './components/ModelsView';
import InventoryView from './components/InventoryView';
import WorkflowsView from './components/WorkflowsView';
import EventStreamView from './components/EventStreamView';
import LogsView from './components/LogsView';
import SettingsView from './components/SettingsView';
import ObservabilityView from './components/ObservabilityView';
import UpdateDiagnosticsView from './components/UpdateDiagnosticsView';
import { fetchHealth, ensureAuthToken } from './services/api';
import './App.css'; // import Vite app stylesheet if any, or keep it empty. We rely on index.css

type Tab = 'home' | 'services' | 'models' | 'inventory' | 'workflows' | 'events' | 'logs' | 'settings' | 'observability' | 'maintenance';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('home');
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [daemonOnline, setDaemonOnline] = useState<boolean>(false);
  const [checkingDaemon, setCheckingDaemon] = useState<boolean>(true);

  // Real-time Toast Notifications state
  const [toasts, setToasts] = useState<{ id: number; message: string; type: 'success' | 'info' | 'warning' | 'error' }[]>([]);
  const [prevStatusMap, setPrevStatusMap] = useState<Record<string, string>>({});

  // Command Palette state
  const [showPalette, setShowPalette] = useState(false);
  const [paletteSearch, setPaletteSearch] = useState('');
  const [paletteIndex, setPaletteIndex] = useState(0);

  const addToast = (message: string, type: 'success' | 'info' | 'warning' | 'error' = 'info') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4500);
  };

  // Poll FastAPI backend health endpoint and detect transitions
  const checkDaemonHealth = async () => {
    try {
      const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8088';
      const token = await ensureAuthToken();
      const headers: Record<string, string> = {};
      if (token) {
        headers["X-API-Key"] = token;
      }
      const [healthRes, servicesRes] = await Promise.all([
        fetchHealth(),
        fetch(`${BASE_URL}/api/v1/services`, { headers }).then(r => r.json())
      ]);
      
      const isOnline = healthRes.status === 'healthy' || healthRes.status === 'running';
      
      if (daemonOnline !== isOnline) {
        addToast(isOnline ? 'Daemon Connection Restored' : 'Daemon Connection Terminated', isOnline ? 'success' : 'error');
      }
      setDaemonOnline(isOnline);

      // Track transition alerts
      if (Array.isArray(servicesRes)) {
        servicesRes.forEach((s: any) => {
          const prev = prevStatusMap[s.id];
          if (prev && prev !== s.status) {
            addToast(`Service '${s.name}' transitioned from ${prev} to ${s.status}`, s.status === 'RUNNING' ? 'success' : 'warning');
          }
          prevStatusMap[s.id] = s.status;
        });
        setPrevStatusMap({ ...prevStatusMap });
      }
    } catch {
      if (daemonOnline) {
        addToast('Daemon Connection Terminated', 'error');
      }
      setDaemonOnline(false);
    } finally {
      setCheckingDaemon(false);
    }
  };

  useEffect(() => {
    checkDaemonHealth();
    const interval = setInterval(checkDaemonHealth, 4000);
    return () => clearInterval(interval);
  }, [daemonOnline, prevStatusMap]);

  // Command palette Ctrl+K keyboard listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setShowPalette(prev => !prev);
        setPaletteSearch('');
        setPaletteIndex(0);
      } else if (e.key === 'Escape') {
        setShowPalette(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Theme Sync
  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
    addToast(`Theme set to ${theme === 'dark' ? 'light' : 'dark'}`, 'info');
  };

  const paletteCommands = paletteCommandsList(setActiveTab, toggleTheme, setToasts, setShowPalette);
  
  const filteredCommands = paletteCommands.filter(c => 
    c.label.toLowerCase().includes(paletteSearch.toLowerCase())
  );

  // Nav items configuration
  const navItems: { id: string; label: string; icon: any; badge?: string }[] = [
    { id: 'home', label: 'Home', icon: Home },
    { id: 'services', label: 'Services', icon: Server },
    { id: 'models', label: 'Models', icon: Layers },
    { id: 'inventory', label: 'Health & Inventory', icon: ShieldCheck },
    { id: 'observability', label: 'Observability', icon: Activity },
    { id: 'workflows', label: 'Workflows', icon: Cpu },
    { id: 'events', label: 'Event Stream', icon: Radio },
    { id: 'logs', label: 'Logs', icon: Terminal },
    { id: 'settings', label: 'Settings & Policies', icon: Settings },
    { id: 'maintenance', label: 'Maintenance', icon: AlertOctagon }
  ];

  const getPageTitle = () => {
    const active = navItems.find(item => item.id === activeTab);
    return active ? active.label : 'Control Plane';
  };

  const renderContent = () => {
    if (!daemonOnline && !checkingDaemon) {
      return (
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center', 
          height: '100%', 
          textAlign: 'center',
          padding: '32px',
          color: 'var(--text-secondary)'
        }}>
          <AlertOctagon size={64} style={{ color: 'var(--color-danger)', marginBottom: '20px' }} />
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '2rem', color: 'var(--text-primary)', fontWeight: 700 }}>
            Control Plane Offline
          </h2>
          <p style={{ marginTop: '8px', maxWidth: '480px' }}>
            Cannot connect to the local AI Control Plane daemon. Please make sure the backend is running.
          </p>
          <div style={{ 
            marginTop: '24px', 
            padding: '12px 18px', 
            backgroundColor: 'var(--bg-secondary)', 
            border: '1px solid var(--border-color)', 
            borderRadius: '6px',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.85rem'
          }}>
            uvicorn src.backend.app.main:app --reload
          </div>
          <button 
            onClick={checkDaemonHealth} 
            style={{ 
              marginTop: '20px', 
              padding: '10px 20px', 
              backgroundColor: 'var(--accent-primary)', 
              color: 'white', 
              border: 'none', 
              borderRadius: '8px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Retry Connection
          </button>
        </div>
      );
    }

    switch (activeTab) {
      case 'home':
        return <HomeView />;
      case 'services':
        return <ServicesView />;
      case 'models':
        return <ModelsView />;
      case 'inventory':
        return <InventoryView />;
      case 'workflows':
        return <WorkflowsView />;
      case 'events':
        return <EventStreamView />;
      case 'logs':
        return <LogsView />;
      case 'settings':
        return <SettingsView />;
      case 'observability':
        return <ObservabilityView />;
      case 'maintenance':
        return <UpdateDiagnosticsView />;
      default:
        return (
          <div style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            justifyContent: 'center', 
            height: '100%', 
            textAlign: 'center' 
          }}>
            <HelpCircle size={48} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', color: 'var(--text-primary)' }}>
              {getPageTitle()} View
            </h2>
            <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
              This tab represents a future Phase 2 capability that will be added in subsequent implementation phases.
            </p>
          </div>
        );
    }
  };

  return (
    <div className="app-container">
      {/* Left Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon">A</div>
          <div className="brand-name">AI Control Plane</div>
        </div>
        
        <nav className="sidebar-menu">
          {navItems.map(item => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <div 
                key={item.id} 
                className={`menu-item ${isActive ? 'active' : ''}`}
                onClick={() => setActiveTab(item.id as Tab)}
              >
                <Icon size={18} />
                <span style={{ flex: 1 }}>{item.label}</span>
                {item.badge && !isActive && (
                  <span style={{ 
                    fontSize: '0.65rem', 
                    padding: '2px 6px', 
                    backgroundColor: 'rgba(255, 255, 255, 0.05)', 
                    borderRadius: '4px',
                    color: 'var(--text-muted)'
                  }}>
                    {item.badge}
                  </span>
                )}
              </div>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div>AI Runtime Manager v1.0.0</div>
          <div style={{ marginTop: '4px' }}>Local Station Orchestration</div>
        </div>
      </aside>

      {/* Main content pane */}
      <main className="main-content">
        <header className="navbar">
          <div className="navbar-title">
            <h1>{getPageTitle()}</h1>
          </div>
          
          <div className="navbar-actions">
            <div className={`daemon-status ${daemonOnline ? '' : 'offline'}`}>
              <div className="status-dot" />
              <span>Daemon: {daemonOnline ? 'Connected' : 'Offline'}</span>
            </div>
            
            <button className="btn-icon" onClick={toggleTheme} title="Toggle Dark/Light Mode">
              {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </div>
        </header>

        {renderContent()}
      </main>

      {/* Toast Notifications */}
      <div className="toast-container">
        {toasts.map(t => (
          <div key={t.id} className={`toast toast-${t.type} animate-slide-in`}>
            <span>{t.message}</span>
            <button className="toast-close" onClick={() => setToasts(prev => prev.filter(x => x.id !== t.id))}>&times;</button>
          </div>
        ))}
      </div>

      {/* Command Palette Ctrl+K */}
      {showPalette && (
        <div className="palette-overlay" onClick={() => setShowPalette(false)}>
          <div className="palette-modal" onClick={e => e.stopPropagation()}>
            <div className="palette-input-container">
              <input 
                type="text" 
                placeholder="Search commands... (e.g. Go to Logs, Toggle theme)"
                value={paletteSearch}
                onChange={e => { setPaletteSearch(e.target.value); setPaletteIndex(0); }}
                autoFocus
                onKeyDown={e => {
                  const commands = paletteCommands.filter(c => 
                    c.label.toLowerCase().includes(paletteSearch.toLowerCase())
                  );
                  if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    setPaletteIndex(prev => (prev + 1) % Math.max(1, commands.length));
                  } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    setPaletteIndex(prev => (prev - 1 + commands.length) % Math.max(1, commands.length));
                  } else if (e.key === 'Enter') {
                    e.preventDefault();
                    if (commands[paletteIndex]) {
                      commands[paletteIndex].action();
                    }
                  }
                }}
              />
            </div>
            <div className="palette-results">
              {filteredCommands.map((c: any, idx: number) => (
                <div 
                  key={idx} 
                  className={`palette-item ${idx === paletteIndex ? 'active' : ''}`}
                  onClick={() => c.action()}
                  onMouseEnter={() => setPaletteIndex(idx)}
                >
                  {c.label}
                </div>
              ))}
              {filteredCommands.length === 0 && (
                <div className="palette-empty">No commands match search keyword.</div>
              )}
            </div>
            <div className="palette-footer">
              <span>↑↓ to navigate</span>
              <span>Enter to select</span>
              <span>Esc to close</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Command palette actions declaration
const paletteCommandsList = (
  setActiveTab: (tab: Tab) => void,
  toggleTheme: () => void,
  setToasts: any,
  setShowPalette: (show: boolean) => void
) => [
  { label: 'Navigate: Go to Home Dashboard', action: () => { setActiveTab('home'); setShowPalette(false); } },
  { label: 'Navigate: Go to Services Lifecycle', action: () => { setActiveTab('services'); setShowPalette(false); } },
  { label: 'Navigate: Go to Models Capability Browser', action: () => { setActiveTab('models'); setShowPalette(false); } },
  { label: 'Navigate: Go to Workstation Inventory', action: () => { setActiveTab('inventory'); setShowPalette(false); } },
  { label: 'Navigate: Go to Observability Metrics', action: () => { setActiveTab('observability'); setShowPalette(false); } },
  { label: 'Navigate: Go to Workflows Stepper', action: () => { setActiveTab('workflows'); setShowPalette(false); } },
  { label: 'Navigate: Go to System Event Stream', action: () => { setActiveTab('events'); setShowPalette(false); } },
  { label: 'Navigate: Go to Central Log Terminal', action: () => { setActiveTab('logs'); setShowPalette(false); } },
  { label: 'Navigate: Go to Settings & Policies', action: () => { setActiveTab('settings'); setShowPalette(false); } },
  { label: 'Navigate: Go to Maintenance & Updates', action: () => { setActiveTab('maintenance'); setShowPalette(false); } },
  { label: 'Action: Toggle Interface Theme', action: () => { toggleTheme(); setShowPalette(false); } },
  { label: 'Action: Flush Notifications Queue', action: () => { setToasts([]); setShowPalette(false); } }
];

export default App;
