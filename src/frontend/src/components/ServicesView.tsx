import { useEffect, useState, useRef } from 'react';
import { 
  Play, Square, RotateCw, Terminal, Cpu, Network, ShieldCheck, Download, Search, X 
} from 'lucide-react';
import { 
  fetchServices, startService, stopService, restartService, 
  fetchServiceLogs, fetchModels 
} from '../services/api';
import type { Service, Model } from '../services/api';

export default function ServicesView() {
  const [services, setServices] = useState<Service[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Service action loading states
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});
  
  // Log viewer modal state
  const [selectedService, setSelectedService] = useState<Service | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [logFilter, setLogFilter] = useState('');
  const [logLimit, setLogLimit] = useState(100);
  const [pollingLogs, setPollingLogs] = useState(false);
  
  const logEndRef = useRef<HTMLDivElement>(null);

  const loadData = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const [servicesData, modelsData] = await Promise.all([
        fetchServices(true), // force backend checks evaluation
        fetchModels()
      ]);
      setServices(servicesData);
      setModels(modelsData);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to query service registries.');
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Poll services status every 4 seconds
    const interval = setInterval(() => {
      loadData(false);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  // Poll logs for the active service log viewer modal
  useEffect(() => {
    let logInterval: any;
    
    if (selectedService && pollingLogs) {
      const getLogs = async () => {
        try {
          const res = await fetchServiceLogs(selectedService.id, logLimit);
          setLogs(res.logs);
        } catch (err) {
          console.error(err);
        }
      };
      
      getLogs();
      logInterval = setInterval(getLogs, 2000);
    }
    
    return () => {
      if (logInterval) clearInterval(logInterval);
    };
  }, [selectedService, pollingLogs, logLimit]);

  // Scroll to bottom when logs load
  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  const handleStart = async (id: string) => {
    setActionLoading(prev => ({ ...prev, [id]: true }));
    try {
      await startService(id);
      await loadData(false);
    } catch (err: any) {
      alert(`Start failed: ${err.message}`);
    } finally {
      setActionLoading(prev => ({ ...prev, [id]: false }));
    }
  };

  const handleStop = async (id: string) => {
    setActionLoading(prev => ({ ...prev, [id]: true }));
    try {
      await stopService(id);
      await loadData(false);
    } catch (err: any) {
      alert(`Stop failed: ${err.message}`);
    } finally {
      setActionLoading(prev => ({ ...prev, [id]: false }));
    }
  };

  const handleRestart = async (id: string) => {
    setActionLoading(prev => ({ ...prev, [id]: true }));
    try {
      await restartService(id);
      await loadData(false);
    } catch (err: any) {
      alert(`Restart failed: ${err.message}`);
    } finally {
      setActionLoading(prev => ({ ...prev, [id]: false }));
    }
  };

  const openLogViewer = (service: Service) => {
    setSelectedService(service);
    setLogs([]);
    setPollingLogs(true);
  };

  const closeLogViewer = () => {
    setSelectedService(null);
    setPollingLogs(false);
    setLogs([]);
    setLogFilter('');
  };

  const downloadLogs = () => {
    if (!selectedService) return;
    const blob = new Blob([logs.join('\n')], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${selectedService.id}_service.log`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'RUNNING': return 'var(--color-success)';
      case 'STARTING': return 'var(--color-info)';
      case 'STOPPED': return 'var(--text-muted)';
      case 'ERROR': return 'var(--color-danger)';
      case 'DEGRADED': return 'var(--color-warning)';
      default: return 'var(--text-secondary)';
    }
  };

  const filteredLogs = logs.filter(line => 
    line.toLowerCase().includes(logFilter.toLowerCase())
  );

  const getServiceModels = (type: string) => {
    return models.filter(m => m.provider === type);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '16px' }}>
        <div className="spinner" />
        <p style={{ color: 'var(--text-secondary)' }}>Polling services status...</p>
      </div>
    );
  }

  return (
    <div className="page-container animate-fade-in" style={{ position: 'relative' }}>
      <div style={{ marginBottom: '28px' }}>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          AI Runtimes & Services
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px' }}>
          Start, stop, restart, and monitor logs for local model engines, routing proxies, and gateways.
        </p>
      </div>

      {error && (
        <div style={{ 
          backgroundColor: 'rgba(239, 68, 68, 0.08)', 
          border: '1px solid rgba(239, 68, 68, 0.2)', 
          color: 'var(--color-danger)', 
          padding: '16px', 
          borderRadius: '8px', 
          marginBottom: '24px',
          fontWeight: 500
        }}>
          {error}
        </div>
      )}

      {/* Services Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '24px' }}>
        {services.map(service => {
          const serviceModels = getServiceModels(service.type);
          const isBusy = actionLoading[service.id];
          const isRunning = service.status === 'RUNNING';
          const isStopped = service.status === 'STOPPED';

          return (
            <div key={service.id} className="card animate-fade-in" style={{ display: 'flex', flexDirection: 'column', height: '100%', borderTop: `4px solid ${getStatusColor(service.status)}` }}>
              
              {/* Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <div>
                  <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {service.name}
                  </h3>
                  <code style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', backgroundColor: 'transparent', padding: 0 }}>
                    ID: {service.id}
                  </code>
                </div>
                
                <span className={`stat-badge`} style={{ 
                  backgroundColor: `rgba(255, 255, 255, 0.03)`, 
                  border: `1px solid ${getStatusColor(service.status)}`, 
                  color: getStatusColor(service.status),
                  fontSize: '0.75rem',
                  padding: '3px 10px',
                  borderRadius: '30px',
                  fontWeight: 700
                }}>
                  {service.status}
                </span>
              </div>

              {/* Specs & Mappings */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', flex: 1, fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Network size={14} color="var(--text-muted)" />
                  <span>Port: <strong>{service.port || 'N/A'}</strong></span>
                </div>
                
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Cpu size={14} color="var(--text-muted)" />
                  <span>PID: <strong>{service.pid || '-'}</strong></span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <ShieldCheck size={14} color="var(--text-muted)" />
                  <span>Auto Start: <strong>{service.auto_start ? 'Enabled' : 'Disabled'}</strong></span>
                </div>

                {service.binary_path && (
                  <div style={{ 
                    marginTop: '8px',
                    padding: '8px', 
                    backgroundColor: 'rgba(0,0,0,0.15)', 
                    border: '1px solid var(--border-color)', 
                    borderRadius: '6px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.75rem',
                    wordBreak: 'break-all'
                  }}>
                    {service.binary_path}
                  </div>
                )}

                {serviceModels.length > 0 && (
                  <div style={{ marginTop: '10px' }}>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px', fontSize: '0.8rem' }}>
                      Loaded Models ({serviceModels.length}):
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {serviceModels.slice(0, 4).map(m => (
                        <span key={m.id} style={{ 
                          fontSize: '0.7rem', 
                          padding: '2px 8px', 
                          backgroundColor: 'var(--border-color)', 
                          borderRadius: '4px',
                          color: 'var(--text-primary)'
                        }}>
                          {m.name}
                        </span>
                      ))}
                      {serviceModels.length > 4 && (
                        <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', alignSelf: 'center' }}>
                          + {serviceModels.length - 4} more
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', gap: '10px', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
                {!isRunning ? (
                  <button 
                    onClick={() => handleStart(service.id)} 
                    disabled={isBusy}
                    style={{ 
                      flex: 1, 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center', 
                      gap: '8px',
                      padding: '10px', 
                      backgroundColor: 'var(--accent-primary)', 
                      color: 'white',
                      border: 'none', 
                      borderRadius: '8px',
                      fontWeight: 600,
                      cursor: 'pointer',
                      opacity: isBusy ? 0.65 : 1
                    }}
                  >
                    <Play size={14} /> Start
                  </button>
                ) : (
                  <button 
                    onClick={() => handleStop(service.id)} 
                    disabled={isBusy}
                    style={{ 
                      flex: 1, 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center', 
                      gap: '8px',
                      padding: '10px', 
                      backgroundColor: 'var(--color-danger)', 
                      color: 'white',
                      border: 'none', 
                      borderRadius: '8px',
                      fontWeight: 600,
                      cursor: 'pointer',
                      opacity: isBusy ? 0.65 : 1
                    }}
                  >
                    <Square size={14} /> Stop
                  </button>
                )}

                <button 
                  onClick={() => handleRestart(service.id)} 
                  disabled={isBusy || isStopped}
                  className="btn-icon"
                  style={{ 
                    width: '42px', 
                    height: '42px', 
                    borderRadius: '8px',
                    borderColor: 'var(--border-color)',
                    opacity: (isBusy || isStopped) ? 0.5 : 1,
                    cursor: (isBusy || isStopped) ? 'not-allowed' : 'pointer'
                  }}
                  title="Restart Runtime"
                >
                  <RotateCw size={14} className={isBusy ? 'spinner' : ''} />
                </button>

                <button 
                  onClick={() => openLogViewer(service)} 
                  className="btn-icon"
                  style={{ width: '42px', height: '42px', borderRadius: '8px' }}
                  title="View Service Output Logs"
                >
                  <Terminal size={14} />
                </button>
              </div>

            </div>
          );
        })}
      </div>

      {/* Log Terminal Overlay Modal */}
      {selectedService && (
        <div style={{ 
          position: 'fixed', 
          top: 0, 
          left: 0, 
          width: '100vw', 
          height: '100vh', 
          backgroundColor: 'rgba(0, 0, 0, 0.75)', 
          backdropFilter: 'blur(4px)',
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          zIndex: 1000,
          padding: '24px'
        }}>
          <div className="animate-fade-in" style={{ 
            backgroundColor: '#05070c', 
            border: '1px solid #1e293b', 
            borderRadius: '12px', 
            width: '100%', 
            maxWidth: '900px', 
            height: '80vh', 
            display: 'flex', 
            flexDirection: 'column', 
            boxShadow: '0 25px 50px -12px rgba(0,0,0,0.5)'
          }}>
            
            {/* Modal Header */}
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between', 
              padding: '16px 24px', 
              borderBottom: '1px solid var(--border-color)' 
            }}>
              <div>
                <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '1.15rem', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Terminal size={18} color="var(--accent-primary)" />
                  {selectedService.name} - Output logs
                </h3>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Active Polling • Auto-scroll enabled
                </p>
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <button 
                  onClick={downloadLogs} 
                  className="btn-icon" 
                  style={{ width: '34px', height: '34px', borderRadius: '6px' }}
                  title="Download logs"
                >
                  <Download size={14} />
                </button>
                
                <button 
                  onClick={closeLogViewer} 
                  className="btn-icon" 
                  style={{ width: '34px', height: '34px', borderRadius: '6px', backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--color-danger)', borderColor: 'rgba(239, 68, 68, 0.2)' }}
                >
                  <X size={14} />
                </button>
              </div>
            </div>

            {/* Controls Row */}
            <div style={{ 
              display: 'flex', 
              gap: '12px', 
              padding: '12px 24px', 
              backgroundColor: 'rgba(255,255,255,0.01)', 
              borderBottom: '1px solid var(--border-color)' 
            }}>
              {/* Search log filter */}
              <div style={{ position: 'relative', flex: 1 }}>
                <Search size={14} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                <input 
                  type="text" 
                  placeholder="Filter log output..."
                  value={logFilter}
                  onChange={e => setLogFilter(e.target.value)}
                  style={{ 
                    width: '100%', 
                    padding: '8px 12px 8px 36px', 
                    backgroundColor: '#0b0f19', 
                    border: '1px solid var(--border-color)', 
                    borderRadius: '6px', 
                    color: 'white',
                    fontSize: '0.85rem',
                    outline: 'none'
                  }}
                />
              </div>

              {/* Line Limit dropdown */}
              <select 
                value={logLimit} 
                onChange={e => setLogLimit(Number(e.target.value))}
                style={{ 
                  padding: '8px 12px', 
                  backgroundColor: '#0b0f19', 
                  border: '1px solid var(--border-color)', 
                  borderRadius: '6px', 
                  color: 'white',
                  fontSize: '0.85rem',
                  outline: 'none'
                }}
              >
                <option value={50}>Last 50 lines</option>
                <option value={100}>Last 100 lines</option>
                <option value={200}>Last 200 lines</option>
                <option value={500}>Last 500 lines</option>
              </select>
            </div>

            {/* Terminal Body */}
            <div style={{ 
              flex: 1, 
              overflowY: 'auto', 
              padding: '24px', 
              fontFamily: 'var(--font-mono)', 
              fontSize: '0.8rem', 
              lineHeight: '1.4', 
              color: '#d4d4d8', 
              backgroundColor: '#020408',
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
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: '40px' }}>
                  {logFilter ? 'No log lines match current filter' : 'Waiting for log console output...'}
                </div>
              )}
              <div ref={logEndRef} />
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
