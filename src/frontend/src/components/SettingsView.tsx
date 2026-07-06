import { useEffect, useState } from 'react';
import { 
  Shield, ToggleLeft, ToggleRight, FileCode, Check, Layers 
} from 'lucide-react';
import { 
  fetchConfig, updateConfig, fetchServices, fetchPlugins 
} from '../services/api';
import type { Service } from '../services/api';

interface PluginMetadata {
  id: string;
  name: string;
  version: string;
  required_dependencies: string[];
  supported_os: string[];
  config_schema: any;
  health_probes: any[];
}

export default function SettingsView() {
  const [services, setServices] = useState<Service[]>([]);
  const [plugins, setPlugins] = useState<PluginMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Settings Form State
  const [autoRestart, setAutoRestart] = useState(true);
  const [restartLimit, setRestartLimit] = useState(3);
  const [liteLlmRequests, setLiteLlmRequests] = useState(0);
  const [savingKey, setSavingKey] = useState<string | null>(null);
  const [savedKey, setSavedKey] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [servicesData, pluginsData] = await Promise.all([
        fetchServices(),
        fetchPlugins()
      ]);
      setServices(servicesData);
      setPlugins(pluginsData);

      // Load keys from Config Repo
      try {
        const ar = await fetchConfig('auto_restart_enabled');
        setAutoRestart(ar.value === 'true');
      } catch {}
      try {
        const al = await fetchConfig('auto_restart_limit');
        setRestartLimit(Number(al.value || '3'));
      } catch {}
      try {
        const lr = await fetchConfig('litellm_active_requests');
        setLiteLlmRequests(Number(lr.value || '0'));
      } catch {}

      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch configuration and policy registries.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSaveConfig = async (key: string, value: string) => {
    setSavingKey(key);
    try {
      await updateConfig({ key, value });
      setSavedKey(key);
      setTimeout(() => setSavedKey(null), 2000);
    } catch (err: any) {
      alert(`Save failed: ${err.message}`);
    } finally {
      setSavingKey(null);
    }
  };

  // Generate YAML representation
  const generateYaml = () => {
    let yaml = `# AI Runtime Manager - Orchestration Specification\n# Generated dynamically at: ${new Date().toLocaleString()}\n\n`;
    
    yaml += `global:\n`;
    yaml += `  auto_restart_enabled: ${autoRestart}\n`;
    yaml += `  auto_restart_limit: ${restartLimit}\n`;
    yaml += `  litellm_active_requests: ${liteLlmRequests}\n\n`;
    
    yaml += `services:\n`;
    services.forEach(s => {
      yaml += `  - id: "${s.id}"\n`;
      yaml += `    name: "${s.name}"\n`;
      yaml += `    type: "${s.type}"\n`;
      yaml += `    port: ${s.port || 'null'}\n`;
      yaml += `    auto_start: ${s.auto_start}\n`;
      yaml += `    args: ${JSON.stringify(s.args)}\n`;
    });
    
    yaml += `\npolicies:\n`;
    yaml += `  - name: "PreventLiteLLMStopWithActiveRequestsPolicy"\n`;
    yaml += `    enabled: true\n`;
    yaml += `    target: "litellm"\n`;
    yaml += `    constraint: "active_requests > 0"\n`;
    yaml += `  - name: "ModelPreferencePolicy"\n`;
    yaml += `    enabled: true\n`;
    yaml += `    routing: "local-first"\n`;
    
    return yaml;
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '16px' }}>
        <div className="spinner" />
        <p style={{ color: 'var(--text-secondary)' }}>Querying server policies configuration...</p>
      </div>
    );
  }

  return (
    <div className="page-container animate-fade-in">
      <div style={{ marginBottom: '28px' }}>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          Settings & Policies
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px' }}>
          Configure global thresholds, manage runtime plugin schemas, and inspect environment specifications.
        </p>
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

      {/* Main Grid: Forms Left, YAML Right */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 400px', gap: '32px', alignItems: 'start' }}>
        
        {/* Left Forms Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Policy Engine Parameters */}
          <div className="card">
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '20px' }}>
              <Shield size={18} color="var(--accent-primary)" />
              Active Policies Configuration
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Auto Restart Toggle */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '12px', borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Reactive Auto-Restart</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    Restart services immediately if they transition to an error state.
                  </div>
                </div>
                <button 
                  onClick={() => {
                    const newVal = !autoRestart;
                    setAutoRestart(newVal);
                    handleSaveConfig('auto_restart_enabled', String(newVal));
                  }}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: autoRestart ? 'var(--color-success)' : 'var(--text-muted)' }}
                >
                  {autoRestart ? <ToggleRight size={36} /> : <ToggleLeft size={36} />}
                </button>
              </div>

              {/* Restart Limit */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '12px', borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Auto-Restart Max Attempts</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    Maximum failed attempts allowed before giving up on restarting.
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <input 
                    type="number" 
                    min="1" 
                    max="10" 
                    value={restartLimit} 
                    onChange={e => setRestartLimit(Number(e.target.value))}
                    style={{ 
                      width: '60px', 
                      padding: '6px', 
                      backgroundColor: '#0b0f19', 
                      border: '1px solid var(--border-color)', 
                      borderRadius: '4px',
                      color: 'white',
                      textAlign: 'center'
                    }}
                  />
                  <button 
                    onClick={() => handleSaveConfig('auto_restart_limit', String(restartLimit))}
                    style={{ 
                      padding: '6px 12px', 
                      backgroundColor: 'var(--accent-primary)', 
                      color: 'white', 
                      border: 'none', 
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    {savingKey === 'auto_restart_limit' ? 'Saving...' : savedKey === 'auto_restart_limit' ? <Check size={12} /> : 'Apply'}
                  </button>
                </div>
              </div>

              {/* Stop Prevention (LiteLLM Active Requests) */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>LiteLLM Active Requests Constraint</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    Mock active requests preventing LiteLLM from stopping (Policy Evaluation).
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <input 
                    type="number" 
                    min="0" 
                    value={liteLlmRequests} 
                    onChange={e => setLiteLlmRequests(Number(e.target.value))}
                    style={{ 
                      width: '60px', 
                      padding: '6px', 
                      backgroundColor: '#0b0f19', 
                      border: '1px solid var(--border-color)', 
                      borderRadius: '4px',
                      color: 'white',
                      textAlign: 'center'
                    }}
                  />
                  <button 
                    onClick={() => handleSaveConfig('litellm_active_requests', String(liteLlmRequests))}
                    style={{ 
                      padding: '6px 12px', 
                      backgroundColor: 'var(--accent-primary)', 
                      color: 'white', 
                      border: 'none', 
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    {savingKey === 'litellm_active_requests' ? 'Saving...' : savedKey === 'litellm_active_requests' ? <Check size={12} /> : 'Apply'}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Plugin Metadata List */}
          <div className="card">
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '20px' }}>
              <Layers size={18} color="var(--accent-secondary)" />
              Plugin Metadata & Configuration Schema
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {plugins.map(p => (
                <div key={p.id} style={{ padding: '16px', backgroundColor: 'rgba(0,0,0,0.1)', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h4 style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.95rem' }}>{p.name}</h4>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>v{p.version}</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
                    Supported OS: <strong>{p.supported_os.join(', ')}</strong>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    Dependencies: <strong>{p.required_dependencies.length > 0 ? p.required_dependencies.join(', ') : 'None'}</strong>
                  </div>
                  
                  {/* Schema Display */}
                  <div style={{ marginTop: '12px', borderTop: '1px dashed rgba(255,255,255,0.05)', paddingTop: '10px' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>Config Schema:</div>
                    <pre style={{ 
                      fontSize: '0.7rem', 
                      backgroundColor: '#020408', 
                      padding: '8px', 
                      borderRadius: '4px', 
                      color: 'var(--accent-primary)',
                      fontFamily: 'var(--font-mono)',
                      overflowX: 'auto'
                    }}>
                      {JSON.stringify(p.config_schema, null, 2)}
                    </pre>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right YAML Column */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>
            <FileCode size={18} color="var(--accent-primary)" />
            Generated configuration
          </h3>
          
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: '1.4' }}>
            Real-time preview of the YAML configuration matching the current control plane engine specification.
          </p>

          <pre style={{ 
            flex: 1, 
            padding: '16px', 
            backgroundColor: '#020409', 
            border: '1px solid var(--border-color)', 
            borderRadius: '8px', 
            fontFamily: 'var(--font-mono)', 
            fontSize: '0.75rem', 
            lineHeight: '1.45', 
            color: '#86efac', 
            overflowX: 'auto',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all'
          }}>
            {generateYaml()}
          </pre>
        </div>

      </div>
    </div>
  );
}
