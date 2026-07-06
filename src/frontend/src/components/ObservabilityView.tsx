import { useEffect, useState } from 'react';
import { 
  Activity, RefreshCw, Cpu, HardDrive, BarChart2 
} from 'lucide-react';
import { fetchHistory, fetchServices, ensureAuthToken } from '../services/api';
import type { Service, HistoryEvent } from '../services/api';

interface PerformanceMetric {
  id: number;
  service_id: string;
  timestamp: string;
  request_path: string | null;
  response_time_ms: number | null;
  status_code: number | null;
  vram_used_bytes: number | null;
  gpu_utilization_pct: number | null;
  cpu_utilization_pct: number;
  ram_used_bytes: number;
}

export default function ObservabilityView() {
  const [history, setHistory] = useState<HistoryEvent[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [metrics, setMetrics] = useState<PerformanceMetric[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const [historyData, servicesData] = await Promise.all([
        fetchHistory(150),
        fetchServices()
      ]);
      
      setHistory(historyData);
      setServices(servicesData);
      
      // Fetch metrics from backend DB
      const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8088';
      const token = await ensureAuthToken();
      const headers: Record<string, string> = {};
      if (token) {
        headers["X-API-Key"] = token;
      }
      const res = await fetch(`${BASE_URL}/api/v1/metrics?limit=50`, { headers });
      if (res.ok) {
        const metricsData = await res.json();
        setMetrics(metricsData);
      }
      
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch observability database logs.');
    } finally {
      if (showLoading) setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(() => {
      loadData(false);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  // Extract restart history
  const restarts = history.filter(e => e.event_type === 'SERVICE_RESTART');
  
  // Extract health change history
  const healthChanges = history.filter(e => e.event_type === 'HEALTH_CHANGE');

  // Helper to generate SVG chart coordinates
  const renderSvgChart = (
    data: number[], 
    width = 500, 
    height = 150, 
    color = 'var(--accent-primary)'
  ) => {
    if (data.length === 0) {
      return (
        <div style={{ height: height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
          Waiting for performance metrics collection...
        </div>
      );
    }

    const max = Math.max(...data, 10);
    const min = 0;
    const padding = 10;
    
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;
    
    const points = data.map((val, idx) => {
      const x = padding + (idx / (data.length - 1 || 1)) * chartWidth;
      const y = padding + chartHeight - ((val - min) / (max - min)) * chartHeight;
      return `${x},${y}`;
    }).join(' ');

    const fillPoints = `${padding},${padding + chartHeight} ${points} ${padding + chartWidth},${padding + chartHeight}`;

    return (
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" style={{ overflow: 'visible' }}>
        <defs>
          <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.2"/>
            <stop offset="100%" stopColor={color} stopOpacity="0.0"/>
          </linearGradient>
        </defs>
        {/* Grids */}
        <line x1={padding} y1={padding} x2={width - padding} y2={padding} stroke="var(--border-color)" strokeDasharray="4" />
        <line x1={padding} y1={padding + chartHeight/2} x2={width - padding} y2={padding + chartHeight/2} stroke="var(--border-color)" strokeDasharray="4" />
        <line x1={padding} y1={padding + chartHeight} x2={width - padding} y2={padding + chartHeight} stroke="var(--border-color)" />

        {/* Fill Area */}
        <polygon points={fillPoints} fill="url(#chartGrad)" />
        
        {/* Stroke Line */}
        <polyline points={points} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        
        {/* Max label */}
        <text x={padding + 5} y={padding + 12} fill="var(--text-muted)" fontSize="9" fontFamily="var(--font-mono)">
          MAX: {max.toFixed(0)}
        </text>
      </svg>
    );
  };

  // Group metrics data chronologically
  const sortedMetrics = [...metrics].reverse();
  const cpuData = sortedMetrics.map(m => m.cpu_utilization_pct);
  const ramData = sortedMetrics.map(m => m.ram_used_bytes / (1024 * 1024 * 1024)); // in GB
  const vramData = sortedMetrics.filter(m => m.vram_used_bytes !== null).map(m => (m.vram_used_bytes || 0) / (1024 * 1024 * 1024));

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '16px' }}>
        <div className="spinner" />
        <p style={{ color: 'var(--text-secondary)' }}>Compiling observability metrics...</p>
      </div>
    );
  }

  return (
    <div className="page-container animate-fade-in">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px' }}>
        <div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Observability Dashboard
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px' }}>
            Tracking metrics for {services.length} registered workstation runtimes and gateways.
          </p>
        </div>
        
        <button 
          onClick={handleRefresh} 
          disabled={refreshing}
          className="btn-icon"
          title="Refresh Metrics"
        >
          <RefreshCw className={refreshing ? 'spinner' : ''} size={18} />
        </button>
      </div>

      {error && (
        <div style={{ 
          backgroundColor: 'rgba(239, 68, 68, 0.08)', 
          border: '1px solid rgba(239, 68, 68, 0.2)', 
          color: 'var(--color-danger)', 
          padding: '16px', 
          borderRadius: '8px', 
          marginBottom: '24px'
        }}>
          {error}
        </div>
      )}

      {/* Grid: Charts top, Logs bottom */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '24px', marginBottom: '24px' }}>
        
        {/* SVG charts */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
          
          {/* CPU Chart */}
          <div className="card">
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Cpu size={16} color="var(--accent-primary)" />
              Service CPU utilization (%)
            </h3>
            <div style={{ marginTop: '16px' }}>
              {renderSvgChart(cpuData, 500, 150, 'var(--accent-primary)')}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '8px' }}>
              <span>Historical trace</span>
              <span>Live feed</span>
            </div>
          </div>

          {/* RAM Chart */}
          <div className="card">
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <HardDrive size={16} color="var(--accent-secondary)" />
              Service RAM allocated (GB)
            </h3>
            <div style={{ marginTop: '16px' }}>
              {renderSvgChart(ramData, 500, 150, 'var(--accent-secondary)')}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '8px' }}>
              <span>Historical trace</span>
              <span>Live feed</span>
            </div>
          </div>

          {/* VRAM Chart */}
          {vramData.length > 0 && (
            <div className="card">
              <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Activity size={16} color="var(--color-info)" />
                Service VRAM utilization (GB)
              </h3>
              <div style={{ marginTop: '16px' }}>
                {renderSvgChart(vramData, 500, 150, 'var(--color-info)')}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '8px' }}>
                <span>Historical trace</span>
                <span>Live feed</span>
              </div>
            </div>
          )}

        </div>

        {/* Histories Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px' }}>
          
          {/* Restart history list */}
          <div className="card">
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>
              <RefreshCw size={16} color="var(--color-warning)" />
              Auto-Restart History ({restarts.length})
            </h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '300px', overflowY: 'auto', paddingRight: '4px' }}>
              {restarts.map(e => (
                <div key={e.id} style={{ padding: '10px 14px', backgroundColor: 'rgba(245,158,11,0.02)', border: '1px solid rgba(245,158,11,0.15)', borderRadius: '6px', fontSize: '0.8rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span style={{ fontWeight: 600, color: 'var(--color-warning)' }}>Restarted: </span>
                    <span style={{ color: 'var(--text-primary)' }}>{e.service_id}</span>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '4px' }}>{e.message}</div>
                  </div>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {new Date(e.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              ))}
              {restarts.length === 0 && (
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '16px', fontSize: '0.8rem' }}>
                  No auto-restart events triggered. Uptime is stable.
                </div>
              )}
            </div>
          </div>

          {/* Health changes list */}
          <div className="card">
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>
              <BarChart2 size={16} color="var(--accent-primary)" />
              Health Transition History
            </h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '300px', overflowY: 'auto', paddingRight: '4px' }}>
              {healthChanges.slice(0, 10).map(e => {
                const isFail = e.severity === 'WARNING' || e.severity === 'ERROR';
                return (
                  <div key={e.id} style={{ padding: '10px 14px', backgroundColor: 'rgba(255,255,255,0.01)', border: '1px solid var(--border-color)', borderRadius: '6px', fontSize: '0.8rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ fontWeight: 600, color: isFail ? 'var(--color-danger)' : 'var(--color-success)' }}>
                        {isFail ? 'Degradation: ' : 'Recovery: '}
                      </span>
                      <span style={{ color: 'var(--text-primary)' }}>{e.message}</span>
                    </div>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)', flexShrink: 0, marginLeft: '12px' }}>
                      {new Date(e.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                );
              })}
              {healthChanges.length === 0 && (
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '16px', fontSize: '0.8rem' }}>
                  No health changes recorded. All services run smoothly.
                </div>
              )}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
