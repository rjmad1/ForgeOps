import { useEffect, useState } from 'react';
import { 
  ShieldCheck, RefreshCw, Terminal, Cpu, Network, CheckCircle, 
  XCircle, FileText 
} from 'lucide-react';
import { fetchInventory, triggerInventoryScan } from '../services/api';
import type { InventoryItem } from '../services/api';

export default function InventoryView() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);

  const loadData = async () => {
    try {
      const data = await fetchInventory();
      setItems(data);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch host inventory metadata.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleScan = async () => {
    setScanning(true);
    try {
      await triggerInventoryScan();
      await loadData();
    } catch (err: any) {
      alert(`Scan failed: ${err.message}`);
    } finally {
      setScanning(false);
    }
  };

  const getCategoryItems = (category: string) => {
    return items.filter(item => item.category.toLowerCase() === category.toLowerCase());
  };

  const renderStatusIcon = (status: boolean) => {
    return status ? 
      <CheckCircle size={16} color="var(--color-success)" /> : 
      <XCircle size={16} color="var(--color-danger)" />;
  };

  const renderRuntimeDetails = (item: InventoryItem) => {
    const val = item.value;
    switch (item.key) {
      case 'python':
        return (
          <div>
            <div>Version: <strong>{val.version}</strong></div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', wordBreak: 'break-all' }}>
              Path: {val.executable}
            </div>
          </div>
        );
      case 'node':
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {renderStatusIcon(val.installed)}
            <span>{val.installed ? `Version: ${val.version}` : 'Not Installed'}</span>
          </div>
        );
      case 'wsl':
        return (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {renderStatusIcon(val.available)}
              <span>{val.available ? 'WSL Enabled' : 'WSL Unavailable'}</span>
            </div>
            {val.available && val.distributions.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '8px' }}>
                {val.distributions.map((d: string) => (
                  <span key={d} style={{ fontSize: '0.7rem', padding: '2px 8px', backgroundColor: 'var(--border-color)', borderRadius: '4px' }}>
                    {d}
                  </span>
                ))}
              </div>
            )}
          </div>
        );
      default:
        return <span>{JSON.stringify(val)}</span>;
    }
  };

  const renderToolDetails = (item: InventoryItem) => {
    const val = item.value;
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {renderStatusIcon(val.installed)}
        <span>{val.installed ? `Version: ${val.version}` : 'Not Installed'}</span>
      </div>
    );
  };

  const renderHardwareDetails = (item: InventoryItem) => {
    const val = item.value;
    if (item.key === 'cuda') {
      return (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {renderStatusIcon(val.available)}
            <span>{val.available ? `CUDA Active (NVCC: ${val.version})` : 'CUDA Unavailable'}</span>
          </div>
          {val.cuda_path && (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', wordBreak: 'break-all' }}>
              Path: {val.cuda_path}
            </div>
          )}
        </div>
      );
    }
    
    if (item.key === 'gpu') {
      return (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {renderStatusIcon(val.has_nvidia_gpu)}
            <span>{val.has_nvidia_gpu ? `NVIDIA GPU Found` : 'No Dedicated GPU'}</span>
          </div>
          {val.has_nvidia_gpu && val.details && (
            <div style={{ marginTop: '8px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              <div>GPU Model: <strong>{val.details.name}</strong></div>
              <div>Driver: <strong>{val.details.driver_version}</strong></div>
              <div>Memory Total: <strong>{val.details.memory_total_mb} MB</strong></div>
            </div>
          )}
        </div>
      );
    }

    return <span>{JSON.stringify(val)}</span>;
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '16px' }}>
        <div className="spinner" />
        <p style={{ color: 'var(--text-secondary)' }}>Loading system inventory mapping...</p>
      </div>
    );
  }

  const runtimes = getCategoryItems('runtime');
  const tools = getCategoryItems('tool');
  const hardware = getCategoryItems('hardware');
  const network = getCategoryItems('network');
  const envVars = getCategoryItems('environment');

  return (
    <div className="page-container animate-fade-in">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px' }}>
        <div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            System Environment & Health
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px' }}>
            Inspect local workstation runtimes, hardware capability mapping, and environment paths.
          </p>
        </div>
        
        <button 
          onClick={handleScan} 
          disabled={scanning}
          style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '8px', 
            padding: '10px 18px', 
            backgroundColor: 'var(--accent-primary)', 
            color: 'white', 
            border: 'none', 
            borderRadius: '8px',
            fontWeight: 600,
            cursor: 'pointer',
            boxShadow: 'var(--shadow-sm)',
            opacity: scanning ? 0.65 : 1
          }}
        >
          <RefreshCw className={scanning ? 'spinner' : ''} size={16} />
          {scanning ? 'Scanning Workstation...' : 'Scan Workstation'}
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

      {/* Main layout grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px' }}>
        
        {/* Runtimes & SDKs */}
        <div className="card">
          <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>
            <Terminal size={18} color="var(--accent-primary)" />
            Runtimes & SDKs
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {runtimes.map(item => (
              <div key={item.key} style={{ paddingBottom: '12px', borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                <div style={{ fontWeight: 600, textTransform: 'capitalize', color: 'var(--text-primary)', marginBottom: '6px' }}>
                  {item.key}
                </div>
                {renderRuntimeDetails(item)}
              </div>
            ))}
          </div>
        </div>

        {/* Development Tools */}
        <div className="card">
          <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>
            <ShieldCheck size={18} color="var(--accent-secondary)" />
            Development Tools
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {tools.map(item => (
              <div key={item.key} style={{ paddingBottom: '12px', borderBottom: '1px solid rgba(255,255,255,0.02)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontWeight: 600, textTransform: 'capitalize', color: 'var(--text-primary)' }}>
                  {item.key}
                </div>
                {renderToolDetails(item)}
              </div>
            ))}
          </div>
        </div>

        {/* Hardware & Accelerators */}
        <div className="card">
          <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>
            <Cpu size={18} color="var(--accent-primary)" />
            Hardware & Accelerators
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {hardware.map(item => (
              <div key={item.key} style={{ paddingBottom: '12px', borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                <div style={{ fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-primary)', marginBottom: '6px' }}>
                  {item.key}
                </div>
                {renderHardwareDetails(item)}
              </div>
            ))}
          </div>
        </div>

        {/* Network Port diagnostics */}
        <div className="card">
          <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>
            <Network size={18} color="var(--accent-secondary)" />
            Network Ports Scan
          </h3>
          {network.map(item => {
            const val = item.value;
            return (
              <div key={item.key} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                  The control plane monitors local ports standard to machine learning daemons:
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {val.probed_ports.map((port: number) => {
                    const inUse = val.in_use.includes(port);
                    return (
                      <div key={port} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', backgroundColor: 'rgba(0,0,0,0.1)', border: '1px solid var(--border-color)', borderRadius: '6px' }}>
                        <span style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>Port {port}</span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', fontWeight: 600, color: inUse ? 'var(--color-danger)' : 'var(--color-success)' }}>
                          <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'currentColor' }} />
                          {inUse ? 'In Use' : 'Available'}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>

        {/* Environment variables */}
        {envVars.map(item => {
          const val = item.value;
          return (
            <div key={item.key} className="card" style={{ gridColumn: '1 / -1' }}>
              <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>
                <FileText size={18} color="var(--accent-primary)" />
                Workspace Environment Variables
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {Object.entries(val).map(([key, value]) => (
                  <div key={key} style={{ display: 'flex', borderBottom: '1px solid rgba(255,255,255,0.01)', paddingBottom: '8px' }}>
                    <div style={{ width: '180px', fontWeight: 600, fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-primary)', flexShrink: 0 }}>
                      {key}
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-secondary)', wordBreak: 'break-all' }}>
                      {String(value)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}

      </div>
    </div>
  );
}
