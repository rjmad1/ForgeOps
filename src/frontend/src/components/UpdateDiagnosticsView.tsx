import { useEffect, useState } from 'react';
import { 
  Download, RefreshCw, ArrowUpCircle, 
  Terminal, CheckCircle, FileText 
} from 'lucide-react';
import { fetchUpdates, triggerUpdate, fetchDiagnosticsReport } from '../services/api';
import type { UpdateCheckResponse } from '../services/api';

export default function UpdateDiagnosticsView() {
  const [updates, setUpdates] = useState<UpdateCheckResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);
  
  // Update state
  const [updatingTarget, setUpdatingTarget] = useState<string | null>(null);
  
  // Diagnostics state
  const [report, setReport] = useState<any | null>(null);
  const [generatingReport, setGeneratingReport] = useState(false);

  const loadData = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const data = await fetchUpdates();
      setUpdates(data);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to reach local daemon updates catalog.');
    } finally {
      if (showLoading) setLoading(false);
      setChecking(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCheckUpdates = () => {
    setChecking(true);
    loadData();
  };

  const handleUpdate = async (target: string) => {
    setUpdatingTarget(target);
    try {
      const res = await triggerUpdate(target);
      alert(res.message);
      await loadData();
    } catch (err: any) {
      alert(`Update failed: ${err.message}. Initiating automated state rollback...`);
    } finally {
      setUpdatingTarget(null);
    }
  };

  const generateReport = async () => {
    setGeneratingReport(true);
    try {
      const res = await fetchDiagnosticsReport();
      setReport(res);
    } catch (err: any) {
      alert(`Report failed: ${err.message}`);
    } finally {
      setGeneratingReport(false);
    }
  };

  const downloadJsonReport = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `workstation_diagnostics_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const downloadMarkdownReport = () => {
    if (!report) return;
    
    let md = `# Workstation Diagnostics Report\n`;
    md += `Generated: ${new Date(report.timestamp).toLocaleString()}\n\n`;
    
    md += `## Registered Services\n`;
    report.services.forEach((s: any) => {
      md += `- **${s.name}** (${s.id}): ${s.status} (PID: ${s.pid || 'N/A'}, Port: ${s.port || 'N/A'})\n`;
    });
    
    md += `\n## Discovered Capabilities & Models\n`;
    report.models.forEach((m: any) => {
      md += `- **${m.name}** [${m.provider}] (${m.type})\n`;
    });
    
    md += `\n## SQLite System Configs\n`;
    Object.entries(report.configs).forEach(([key, val]) => {
      md += `- \`${key}\`: \`${val}\`\n`;
    });
    
    md += `\n## System Environment Details\n`;
    report.inventory.forEach((i: any) => {
      md += `### ${i.key.toUpperCase()} (${i.category})\n`;
      md += `\`\`\`json\n${JSON.stringify(i.value, null, 2)}\n\`\`\`\n\n`;
    });
    
    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `workstation_diagnostics_${new Date().toISOString().split('T')[0]}.md`;
    link.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '16px' }}>
        <div className="spinner" />
        <p style={{ color: 'var(--text-secondary)' }}>Scanning package catalogs...</p>
      </div>
    );
  }

  return (
    <div className="page-container animate-fade-in">
      <div style={{ marginBottom: '28px' }}>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          Maintenance & Diagnostics
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px' }}>
          One-click version updates, dependency validation, and workstation diagnostic report generators.
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

      {/* Main Grid split: Update panel left, Diagnostics panel right */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px', alignItems: 'start' }}>
        
        {/* Update Panel Card */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ArrowUpCircle size={18} color="var(--accent-primary)" />
              Update Center
            </h3>
            <button 
              onClick={handleCheckUpdates} 
              disabled={checking}
              className="btn-icon"
              title="Check for Updates"
            >
              <RefreshCw className={checking ? 'spinner' : ''} size={14} />
            </button>
          </div>

          {updates && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {Object.entries(updates).map(([name, status]) => {
                const upToDate = status.current_version === status.latest_version;
                const isUpdating = updatingTarget === name;
                
                return (
                  <div key={name} style={{ 
                    padding: '16px', 
                    backgroundColor: 'rgba(0,0,0,0.1)', 
                    border: '1px solid var(--border-color)', 
                    borderRadius: '8px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <div>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)', textTransform: 'capitalize' }}>
                        {name}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        Installed: <strong>{status.current_version || 'Not Installed'}</strong>
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '2px' }}>
                        Latest Available: <strong>{status.latest_version}</strong>
                      </div>
                    </div>

                    <div>
                      {upToDate && status.installed ? (
                        <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', color: 'var(--color-success)', fontWeight: 600 }}>
                          <CheckCircle size={14} /> Up to Date
                        </span>
                      ) : (
                        <button 
                          onClick={() => handleUpdate(name)}
                          disabled={isUpdating}
                          style={{ 
                            padding: '8px 14px', 
                            backgroundColor: 'var(--accent-primary)', 
                            color: 'white', 
                            border: 'none', 
                            borderRadius: '6px',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px'
                          }}
                        >
                          {isUpdating ? (
                            <>
                              <RefreshCw size={12} className="spinner" />
                              Updating...
                            </>
                          ) : (
                            <>
                              <ArrowUpCircle size={12} />
                              {status.installed ? 'Update' : 'Install'}
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Diagnostics Center Card */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <FileText size={18} color="var(--accent-secondary)" />
              Diagnostics Center
            </h3>
          </div>

          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
            Compile a comprehensive state bundle including services configurations, hardware specs, network bindings, and system limits.
          </p>

          <button 
            onClick={generateReport}
            disabled={generatingReport}
            style={{ 
              padding: '12px', 
              backgroundColor: 'var(--accent-secondary)', 
              color: 'white', 
              border: 'none', 
              borderRadius: '8px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px'
            }}
          >
            {generatingReport ? (
              <>
                <RefreshCw size={16} className="spinner" />
                Compiling Report...
              </>
            ) : (
              <>
                <Terminal size={16} />
                Generate Diagnostics Report
              </>
            )}
          </button>

          {report && (
            <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button 
                  onClick={downloadJsonReport}
                  style={{ 
                    flex: 1, 
                    padding: '8px 12px', 
                    backgroundColor: 'rgba(255,255,255,0.02)', 
                    color: 'white', 
                    border: '1px solid var(--border-color)', 
                    borderRadius: '6px',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px'
                  }}
                >
                  <Download size={12} /> JSON Export
                </button>
                <button 
                  onClick={downloadMarkdownReport}
                  style={{ 
                    flex: 1, 
                    padding: '8px 12px', 
                    backgroundColor: 'rgba(255,255,255,0.02)', 
                    color: 'white', 
                    border: '1px solid var(--border-color)', 
                    borderRadius: '6px',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '6px'
                  }}
                >
                  <Download size={12} /> Markdown Export
                </button>
              </div>

              {/* Collapsible preview */}
              <div>
                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '6px' }}>Report Preview:</div>
                <pre style={{ 
                  maxHeight: '200px', 
                  overflowY: 'auto', 
                  fontSize: '0.7rem', 
                  backgroundColor: '#020409', 
                  padding: '12px', 
                  borderRadius: '6px', 
                  color: 'var(--accent-secondary)',
                  fontFamily: 'var(--font-mono)',
                  border: '1px solid var(--border-color)'
                }}>
                  {JSON.stringify(report, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
