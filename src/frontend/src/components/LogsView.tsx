import { useEffect, useState, useRef } from 'react';
import { 
  Terminal, Search, Download, RefreshCw, AlertTriangle, FileText 
} from 'lucide-react';
import { fetchServices, fetchServiceLogs } from '../services/api';
import type { Service } from '../services/api';

export default function LogsView() {
  const [services, setServices] = useState<Service[]>([]);
  const [selectedServiceId, setSelectedServiceId] = useState<string>('');
  const [logs, setLogs] = useState<string[]>([]);
  const [logPath, setLogPath] = useState<string>('');
  const [logFilter, setLogFilter] = useState('');
  const [logLimit, setLogLimit] = useState(150);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [polling, setPolling] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const logEndRef = useRef<HTMLDivElement>(null);

  // Load services
  const loadServices = async () => {
    try {
      const data = await fetchServices();
      setServices(data);
      if (data.length > 0 && !selectedServiceId) {
        setSelectedServiceId(data[0].id);
      }
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch registered service list.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadServices();
  }, []);

  // Poll service logs
  const loadLogs = async (showRefreshState = false) => {
    if (!selectedServiceId) return;
    if (showRefreshState) setRefreshing(true);
    
    try {
      const res = await fetchServiceLogs(selectedServiceId, logLimit);
      setLogs(res.logs);
      if (res.log_file_path) {
        setLogPath(res.log_file_path);
      }
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(`Failed to read log file output for '${selectedServiceId}'.`);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadLogs();
    
    let interval: any;
    if (selectedServiceId && polling) {
      interval = setInterval(() => {
        loadLogs();
      }, 2000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [selectedServiceId, polling, logLimit]);

  // Scroll to bottom
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  const downloadLogs = () => {
    if (!selectedServiceId || logs.length === 0) return;
    const blob = new Blob([logs.join('\n')], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${selectedServiceId}_daemon_console.log`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const filteredLogs = logs.filter(line => 
    line.toLowerCase().includes(logFilter.toLowerCase())
  );

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '16px' }}>
        <div className="spinner" />
        <p style={{ color: 'var(--text-secondary)' }}>Accessing workstation logs registry...</p>
      </div>
    );
  }

  const activeService = services.find(s => s.id === selectedServiceId);

  return (
    <div className="page-container animate-fade-in" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)' }}>
      {/* Header controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexShrink: 0 }}>
        <div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            System Log Console
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px' }}>
            Consolidated logging dashboard for Windows service runtimes and gateways.
          </p>
        </div>
      </div>

      {error && (
        <div style={{ 
          backgroundColor: 'rgba(239, 68, 68, 0.08)', 
          border: '1px solid rgba(239, 68, 68, 0.2)', 
          color: 'var(--color-danger)', 
          padding: '16px', 
          borderRadius: '8px', 
          marginBottom: '24px',
          flexShrink: 0
        }}>
          {error}
        </div>
      )}

      {/* Main logs terminal pane layout */}
      <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: 0 }}>
        
        {/* Terminal Header Bar */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          padding: '16px 24px', 
          backgroundColor: '#0a0f1d', 
          borderBottom: '1px solid var(--border-color)',
          flexWrap: 'wrap',
          gap: '16px',
          flexShrink: 0
        }}>
          {/* Service Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Terminal size={18} color="var(--accent-primary)" />
            <select 
              value={selectedServiceId} 
              onChange={e => { setSelectedServiceId(e.target.value); setLogs([]); }}
              style={{ 
                padding: '8px 16px', 
                backgroundColor: '#121829', 
                border: '1px solid var(--border-color)', 
                borderRadius: '8px', 
                color: 'white',
                fontSize: '0.9rem',
                fontWeight: 600,
                outline: 'none'
              }}
            >
              {services.map(s => (
                <option key={s.id} value={s.id}>{s.name} ({s.id})</option>
              ))}
            </select>
            
            {activeService && (
              <span className={`stat-badge`} style={{ 
                backgroundColor: 'rgba(255,255,255,0.01)', 
                border: '1px solid rgba(255,255,255,0.1)', 
                fontSize: '0.75rem',
                padding: '4px 10px',
                color: 'var(--text-secondary)'
              }}>
                Status: {activeService.status}
              </span>
            )}
          </div>

          {/* Action buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {/* Polling toggle */}
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: 'var(--text-secondary)', cursor: 'pointer' }}>
              <input 
                type="checkbox" 
                checked={polling} 
                onChange={e => setPolling(e.target.checked)}
                style={{ accentColor: 'var(--accent-primary)' }}
              />
              Live Polling
            </label>

            <button 
              onClick={() => loadLogs(true)} 
              disabled={refreshing}
              className="btn-icon" 
              style={{ width: '36px', height: '36px', borderRadius: '6px' }}
              title="Force Refresh"
            >
              <RefreshCw className={refreshing ? 'spinner' : ''} size={14} />
            </button>

            <button 
              onClick={downloadLogs} 
              disabled={logs.length === 0}
              className="btn-icon" 
              style={{ width: '36px', height: '36px', borderRadius: '6px' }}
              title="Download Logs"
            >
              <Download size={14} />
            </button>
          </div>
        </div>

        {/* Filter bar */}
        <div style={{ 
          display: 'flex', 
          gap: '16px', 
          padding: '12px 24px', 
          backgroundColor: '#070a14', 
          borderBottom: '1px solid var(--border-color)',
          flexShrink: 0
        }}>
          {/* Search filter */}
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input 
              type="text" 
              placeholder="Search console strings..."
              value={logFilter}
              onChange={e => setLogFilter(e.target.value)}
              style={{ 
                width: '100%', 
                padding: '8px 12px 8px 36px', 
                backgroundColor: '#121829', 
                border: '1px solid var(--border-color)', 
                borderRadius: '6px', 
                color: 'white',
                fontSize: '0.85rem',
                outline: 'none'
              }}
            />
          </div>

          {/* Limit selector */}
          <select 
            value={logLimit} 
            onChange={e => setLogLimit(Number(e.target.value))}
            style={{ 
              padding: '8px 12px', 
              backgroundColor: '#121829', 
              border: '1px solid var(--border-color)', 
              borderRadius: '6px', 
              color: 'white',
              fontSize: '0.85rem',
              outline: 'none'
            }}
          >
            <option value={50}>Last 50 lines</option>
            <option value={150}>Last 150 lines</option>
            <option value={300}>Last 300 lines</option>
            <option value={600}>Last 600 lines</option>
          </select>
        </div>

        {/* Console view terminal body */}
        <div style={{ 
          flex: 1, 
          overflowY: 'auto', 
          padding: '24px', 
          fontFamily: 'var(--font-mono)', 
          fontSize: '0.8rem', 
          lineHeight: '1.45', 
          color: '#e4e4e7', 
          backgroundColor: '#020409',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px'
        }}>
          {filteredLogs.map((line, idx) => (
            <div key={idx} style={{ 
              whiteSpace: 'pre-wrap', 
              wordBreak: 'break-all',
              borderLeft: line.toLowerCase().includes('error') ? '2px solid var(--color-danger)' : line.toLowerCase().includes('warn') ? '2px solid var(--color-warning)' : 'none',
              paddingLeft: line.toLowerCase().includes('error') || line.toLowerCase().includes('warn') ? '8px' : '0'
            }}>
              {line}
            </div>
          ))}
          
          {filteredLogs.length === 0 && (
            <div style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '40px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
              <AlertTriangle size={24} />
              <span>{logFilter ? 'No lines match active query filter' : 'No service logs captured yet.'}</span>
            </div>
          )}
          
          <div ref={logEndRef} />
        </div>

        {/* Terminal path footer status */}
        {logPath && (
          <div style={{ 
            padding: '8px 24px', 
            backgroundColor: '#0a0f1d', 
            borderTop: '1px solid var(--border-color)', 
            fontSize: '0.7rem', 
            color: 'var(--text-muted)', 
            display: 'flex', 
            alignItems: 'center', 
            gap: '6px',
            flexShrink: 0
          }}>
            <FileText size={12} />
            <span>Path: <strong>{logPath}</strong></span>
          </div>
        )}

      </div>
    </div>
  );
}
