import { useEffect, useState, type ReactNode } from 'react';
import { 
  Activity, Cpu, HardDrive, ShieldAlert, CheckCircle, AlertTriangle, 
  RefreshCw, Server, Layers, Clock 
} from 'lucide-react';
import { 
  fetchSystemMetrics, fetchServices, fetchModels, fetchHistory
} from '../services/api';
import type { SystemMetrics, Service, Model, HistoryEvent } from '../services/api';

export default function HomeView() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [services, setServices] = useState<Service[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [events, setEvents] = useState<HistoryEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const [metricsData, servicesData, modelsData, historyData] = await Promise.all([
        fetchSystemMetrics(),
        fetchServices(),
        fetchModels(),
        fetchHistory(8)
      ]);
      
      setMetrics(metricsData);
      setServices(servicesData);
      setModels(modelsData);
      setEvents(historyData);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Connection failure: Unable to fetch dashboard telemetry.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    // Poll system metrics and services every 3 seconds
    const interval = setInterval(() => {
      loadData();
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const getOverallHealth = () => {
    if (services.length === 0) return { label: 'Unknown', color: 'stopped', icon: AlertTriangle };
    const hasError = services.some(s => s.status === 'ERROR');
    const allStopped = services.every(s => s.status === 'STOPPED');
    if (hasError) {
      return { label: 'Degraded', color: 'error', icon: ShieldAlert };
    }
    if (allStopped) {
      return { label: 'Stopped', color: 'stopped', icon: AlertTriangle };
    }
    return { label: 'Healthy', color: 'running', icon: CheckCircle };
  };

  const healthInfo = getOverallHealth();
  const HealthIcon = healthInfo.icon;

  const renderGauge = (percentage: number, title: string, subtitle: string, icon: ReactNode) => {
    const radius = 36;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;
    
    let colorClass = '';
    if (percentage > 85) colorClass = 'danger';
    else if (percentage > 60) colorClass = 'warning';

    return (
      <div className="card metric-card animate-fade-in">
        <div className="metric-details">
          <span className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {icon} {title}
          </span>
          <div className="metric-value">{percentage.toFixed(0)}%</div>
          <div className="metric-label">{subtitle}</div>
        </div>
        <div style={{ position: 'relative', width: '90px', height: '90px' }}>
          <svg className="gauge-svg" width="90" height="90" viewBox="0 0 90 90">
            <circle className="gauge-bg" cx="45" cy="45" r={radius} />
            <circle 
              className={`gauge-fill ${colorClass}`} 
              cx="45" 
              cy="45" 
              r={radius} 
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
            />
          </svg>
        </div>
      </div>
    );
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '16px' }}>
        <div className="spinner" />
        <p style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>Initializing Control Plane telemetry...</p>
      </div>
    );
  }

  return (
    <div className="page-container animate-fade-in">
      {/* Top dashboard summary header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px' }}>
        <div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '12px' }}>
            Workstation Status
            <span className={`stat-badge ${healthInfo.color}`} style={{ fontSize: '0.8rem', padding: '4px 12px', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
              <HealthIcon size={12} />
              {healthInfo.label}
            </span>
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px' }}>
            Local machine resource allocation and AI services overview.
          </p>
        </div>
        
        <button 
          onClick={handleRefresh} 
          className="btn-icon" 
          disabled={refreshing}
          title="Refresh Telemetry"
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
          marginBottom: '24px',
          fontWeight: 500,
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <ShieldAlert size={20} />
          {error}
        </div>
      )}

      {/* Resource Gauge Grid */}
      <div className="grid-container grid-cols-4" style={{ marginBottom: '32px' }}>
        {renderGauge(
          metrics?.cpu.utilization_pct || 0,
          'CPU Load',
          'Host logical cores',
          <Cpu size={16} color="var(--accent-primary)" />
        )}
        {renderGauge(
          metrics?.ram.utilization_pct || 0,
          'RAM Usage',
          metrics ? `${formatBytes(metrics.ram.used_bytes)} / ${formatBytes(metrics.ram.total_bytes)}` : 'Allocated memory',
          <HardDrive size={16} color="var(--accent-primary)" />
        )}
        {metrics?.gpu.available ? (
          <>
            {renderGauge(
              metrics.gpu.utilization_pct,
              'GPU Load',
              metrics.gpu.name,
              <Activity size={16} color="var(--accent-secondary)" />
            )}
            {renderGauge(
              (metrics.gpu.vram_used_bytes / metrics.gpu.vram_total_bytes) * 100,
              'VRAM Usage',
              metrics ? `${formatBytes(metrics.gpu.vram_used_bytes)} / ${formatBytes(metrics.gpu.vram_total_bytes)}` : 'Video memory',
              <Layers size={16} color="var(--accent-secondary)" />
            )}
          </>
        ) : (
          <div className="card metric-card animate-fade-in" style={{ opacity: 0.65, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
            <Activity size={32} style={{ color: 'var(--text-muted)', marginBottom: '8px' }} />
            <span className="card-title" style={{ margin: 0 }}>GPU Unavailable</span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '4px' }}>No compatible NVIDIA GPU found</span>
          </div>
        )}
      </div>

      <div className="grid-container grid-cols-2">
        {/* Left Column: Services list & Models Summary */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Services status widget */}
          <div className="card">
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>
              <Server size={18} color="var(--accent-primary)" />
              Active Run-times
            </h3>
            <div className="stat-list">
              {services.map(service => (
                <div key={service.id} className="stat-item">
                  <div>
                    <div className="stat-name">{service.name}</div>
                    <div className="stat-sub">
                      Type: {service.type} {service.port ? `| Port: ${service.port}` : ''}
                    </div>
                  </div>
                  <span className={`stat-badge ${service.status.toLowerCase()}`}>
                    {service.status}
                  </span>
                </div>
              ))}
              {services.length === 0 && (
                <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '12px' }}>
                  No service runtimes registered.
                </p>
              )}
            </div>
          </div>

          {/* Model capabilities summary */}
          <div className="card">
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>
              <Layers size={18} color="var(--accent-secondary)" />
              Discovered Models ({models.length})
            </h3>
            <div className="stat-list">
              {models.slice(0, 3).map(model => (
                <div key={model.id} className="stat-item">
                  <div>
                    <div className="stat-name">{model.name}</div>
                    <div className="stat-sub">Provider: {model.provider} | Type: {model.type}</div>
                  </div>
                  <span className="stat-badge" style={{ backgroundColor: 'var(--border-color)', color: 'var(--text-secondary)' }}>
                    {model.metadata.parameter_size || 'Dynamic'}
                  </span>
                </div>
              ))}
              {models.length === 0 && (
                <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '12px' }}>
                  No models discovered on local machine.
                </p>
              )}
              {models.length > 3 && (
                <div style={{ textAlign: 'center', fontSize: '0.85rem', color: 'var(--accent-primary)', fontWeight: 600, cursor: 'pointer', marginTop: '4px' }}>
                  + {models.length - 3} more models discovered
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Recent Operational History log stream */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px', flexShrink: 0 }}>
            <Clock size={18} color="var(--accent-primary)" />
            Recent Events
          </h3>
          
          <div className="history-feed" style={{ flex: 1, overflowY: 'auto', maxHeight: '420px', paddingRight: '4px' }}>
            {events.map(event => (
              <div key={event.id} className="history-item">
                <span className={`severity-indicator ${event.severity.toLowerCase()}`}>
                  {event.severity === 'ERROR' ? <ShieldAlert size={14} /> : event.severity === 'WARNING' ? <AlertTriangle size={14} /> : <CheckCircle size={14} />}
                </span>
                <div className="history-content">
                  <div className="history-message">{event.message}</div>
                  <div className="history-meta">
                    <span className="history-tag">{event.event_type}</span>
                    <span className="history-timestamp">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              </div>
            ))}
            {events.length === 0 && (
              <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '24px', display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                No recent system events logged.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
