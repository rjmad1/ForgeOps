import { useEffect, useState } from 'react';
import { 
  CheckCircle2, XCircle, RotateCcw, AlertTriangle, 
  Clock, Play, Loader, ShieldAlert 
} from 'lucide-react';
import { fetchHistory } from '../services/api';
import type { HistoryEvent } from '../services/api';

interface Step {
  id: string;
  name: string;
  desc: string;
  rollbackDesc: string;
}

export default function WorkflowsView() {
  const [history, setHistory] = useState<HistoryEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Interactive Simulation state
  const [selectedWorkflow, setSelectedWorkflow] = useState<'start' | 'stop'>('start');
  const [simState, setSimState] = useState<'idle' | 'running' | 'failed' | 'completed' | 'rolling-back'>('idle');
  const [activeStepIdx, setActiveStepIdx] = useState<number>(-1);
  const [failStepIdx, setFailStepIdx] = useState<number>(-1);

  const startSteps: Step[] = [
    { id: 'preflight', name: 'Pre-flight Verification', desc: 'Checks OS support, binary availability, and locks port.', rollbackDesc: 'No rollback needed' },
    { id: 'status-starting', name: 'Update Status to STARTING', desc: 'Saves status state as STARTING in sqlite registry.', rollbackDesc: 'Reverts status to ERROR, clears PID' },
    { id: 'launch', name: 'Launch Subprocess', desc: 'Spawns executable on Windows and redirects stdout/stderr.', rollbackDesc: 'Kills spawned PID and children recursively' },
    { id: 'port', name: 'Wait for Port to Respond', desc: 'Polls the TCP port/API ping for responsiveness (5s limit).', rollbackDesc: 'Triggers shutdown of launched process' },
    { id: 'discovery', name: 'Run Capabilities Discovery', desc: 'Pulls loaded models or tools and syncs capability registry.', rollbackDesc: 'Clears recently indexed capabilities' },
    { id: 'status-running', name: 'Update Status to RUNNING', desc: 'Saves status state as RUNNING in sqlite registry.', rollbackDesc: 'Reverts status to ERROR' }
  ];

  const stopSteps: Step[] = [
    { id: 'status-stopping', name: 'Update Status to STOPPING', desc: 'Saves status state as STOPPING in registry.', rollbackDesc: 'Reverts status to RUNNING' },
    { id: 'stop-proc', name: 'Stop Subprocess', desc: 'Terminates parent PID and descendants gracefully, then forcefully.', rollbackDesc: 'No rollback action possible' },
    { id: 'status-stopped', name: 'Update Status to STOPPED', desc: 'Saves status state as STOPPED in registry.', rollbackDesc: 'Reverts status to RUNNING' }
  ];

  const activeSteps = selectedWorkflow === 'start' ? startSteps : stopSteps;

  const loadData = async () => {
    try {
      const data = await fetchHistory(50);
      const filtered = data.filter(e => 
        e.event_type === 'WORKFLOW_EXECUTION' || e.event_type === 'SERVICE_RESTART'
      );
      setHistory(filtered);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to load workflow run records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Simulation execution loop
  const runSimulation = async (failAtIdx = -1) => {
    setSimState('running');
    setFailStepIdx(failAtIdx);
    
    for (let i = 0; i < activeSteps.length; i++) {
      setActiveStepIdx(i);
      
      // Delay to simulate progress
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      if (failAtIdx === i) {
        setSimState('rolling-back');
        // Rollback animation back through completed steps
        for (let j = i; j >= 0; j--) {
          setActiveStepIdx(j);
          await new Promise(resolve => setTimeout(resolve, 800));
        }
        setSimState('failed');
        setActiveStepIdx(-1);
        return;
      }
    }
    
    setSimState('completed');
    setActiveStepIdx(-1);
  };

  const resetSimulation = () => {
    setSimState('idle');
    setActiveStepIdx(-1);
    setFailStepIdx(-1);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '16px' }}>
        <div className="spinner" />
        <p style={{ color: 'var(--text-secondary)' }}>Querying workflow execution history...</p>
      </div>
    );
  }

  return (
    <div className="page-container animate-fade-in">
      <div style={{ marginBottom: '28px' }}>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
          Workflow Visualizer
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px' }}>
          Inspect the atomic orchestration steps of startup/shutdown pipelines, rollbacks, and diagnostics.
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

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '32px', alignItems: 'start' }}>
        
        {/* Step Flow Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="card">
            {/* Visual Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '16px', marginBottom: '24px' }}>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button 
                  onClick={() => { setSelectedWorkflow('start'); resetSimulation(); }}
                  style={{ 
                    padding: '8px 16px', 
                    backgroundColor: selectedWorkflow === 'start' ? 'var(--accent-primary)' : 'rgba(255,255,255,0.02)', 
                    color: 'white', 
                    border: selectedWorkflow === 'start' ? 'none' : '1px solid var(--border-color)',
                    borderRadius: '6px',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  Start Service Pipeline
                </button>
                <button 
                  onClick={() => { setSelectedWorkflow('stop'); resetSimulation(); }}
                  style={{ 
                    padding: '8px 16px', 
                    backgroundColor: selectedWorkflow === 'stop' ? 'var(--accent-primary)' : 'rgba(255,255,255,0.02)', 
                    color: 'white', 
                    border: selectedWorkflow === 'stop' ? 'none' : '1px solid var(--border-color)',
                    borderRadius: '6px',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  Stop Service Pipeline
                </button>
              </div>

              {/* Simulation triggers */}
              <div style={{ display: 'flex', gap: '8px' }}>
                {simState === 'idle' ? (
                  <>
                    <button 
                      onClick={() => runSimulation()}
                      style={{ padding: '6px 12px', backgroundColor: 'var(--color-success)', color: 'white', border: 'none', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
                    >
                      <Play size={12} /> Simulate Success
                    </button>
                    {selectedWorkflow === 'start' && (
                      <button 
                        onClick={() => runSimulation(3)} // fail at "Wait for Port"
                        style={{ padding: '6px 12px', backgroundColor: 'var(--color-danger)', color: 'white', border: 'none', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
                      >
                        <ShieldAlert size={12} /> Simulate Port Failure
                      </button>
                    )}
                  </>
                ) : (
                  <button 
                    onClick={resetSimulation}
                    disabled={simState === 'running' || simState === 'rolling-back'}
                    style={{ padding: '6px 12px', backgroundColor: 'var(--border-color)', color: 'var(--text-primary)', border: '1px solid var(--border-color)', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer' }}
                  >
                    Reset Visual
                  </button>
                )}
              </div>
            </div>

            {/* Stepper Timeline UI */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', position: 'relative' }}>
              
              {/* Stepper vertical line indicator */}
              <div style={{ 
                position: 'absolute', 
                left: '19px', 
                top: '12px', 
                bottom: '12px', 
                width: '2px', 
                backgroundColor: 'var(--border-color)', 
                zIndex: 0 
              }} />

              {activeSteps.map((step, idx) => {
                const isActive = activeStepIdx === idx;
                const isCompleted = simState === 'completed' || (simState === 'running' && idx < activeStepIdx) || (simState === 'rolling-back' && idx < activeStepIdx);
                const isFailed = failStepIdx === idx && (simState === 'failed' || simState === 'rolling-back');
                const isRollingBack = simState === 'rolling-back' && activeStepIdx === idx;
                
                let stepColor = 'var(--text-muted)';
                let iconNode = <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'currentColor' }} />;
                let containerBorder = 'none';

                if (isActive) {
                  stepColor = 'var(--accent-primary)';
                  iconNode = <Loader className="spinner" style={{ width: '14px', height: '14px', borderTopColor: 'white' }} />;
                  containerBorder = '1px solid var(--accent-primary)';
                } else if (isRollingBack) {
                  stepColor = 'var(--color-warning)';
                  iconNode = <RotateCcw size={14} className="spinner" style={{ animationDuration: '2s', border: 'none' }} />;
                  containerBorder = '1px solid var(--color-warning)';
                } else if (isCompleted) {
                  stepColor = 'var(--color-success)';
                  iconNode = <CheckCircle2 size={16} />;
                } else if (isFailed) {
                  stepColor = 'var(--color-danger)';
                  iconNode = <XCircle size={16} />;
                  containerBorder = '1px solid var(--color-danger)';
                }

                return (
                  <div key={step.id} style={{ 
                    display: 'flex', 
                    gap: '20px', 
                    zIndex: 1, 
                    padding: '12px 16px', 
                    borderRadius: '8px',
                    backgroundColor: isActive || isRollingBack || isFailed ? 'rgba(255,255,255,0.01)' : 'transparent',
                    border: containerBorder,
                    opacity: (simState !== 'idle' && !isActive && !isCompleted && !isFailed && !isRollingBack) ? 0.45 : 1,
                    transition: 'all 0.2s ease'
                  }}>
                    {/* Stepper Circle Indicator */}
                    <div style={{ 
                      width: '8px', 
                      height: '8px', 
                      borderRadius: '50%', 
                      border: '6px solid var(--bg-secondary)', 
                      boxSizing: 'content-box',
                      backgroundColor: stepColor,
                      color: stepColor,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: isActive ? '0 0 10px var(--accent-glow)' : 'none',
                      marginTop: '2px'
                    }}>
                      {iconNode}
                    </div>
                    
                    {/* Step descriptions */}
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, color: isActive ? 'var(--accent-primary)' : isFailed ? 'var(--color-danger)' : isRollingBack ? 'var(--color-warning)' : 'var(--text-primary)', fontSize: '0.95rem' }}>
                        {step.name}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        {step.desc}
                      </div>
                      
                      {/* Rollback Details visualization */}
                      {(isFailed || isRollingBack || (simState === 'failed' && idx < failStepIdx)) && (
                        <div style={{ 
                          marginTop: '8px', 
                          padding: '6px 10px', 
                          backgroundColor: 'rgba(245,158,11,0.04)', 
                          border: '1px dashed rgba(245,158,11,0.2)', 
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                          color: 'var(--color-warning)',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px'
                        }}>
                          <RotateCcw size={12} />
                          <span>Rollback: <strong>{step.rollbackDesc}</strong></span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Timeline history sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Diagnostics summary card */}
          <div className="card" style={{ backgroundColor: 'rgba(239, 68, 68, 0.02)', borderColor: 'rgba(239, 68, 68, 0.1)' }}>
            <h4 style={{ color: 'var(--color-danger)', fontWeight: 600, fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <AlertTriangle size={14} /> Pipeline Rollbacks
            </h4>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '6px', lineHeight: '1.4' }}>
              If a startup step fails (e.g. port already bound, API endpoint timeouts), the engine immediately rolls back preceding steps in reverse order (e.g. kills spawned process) to maintain workstation clean state.
            </p>
          </div>

          {/* Real history run list */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', maxHeight: '480px' }}>
            <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>
              <Clock size={16} color="var(--accent-primary)" />
              Execution Logs
            </h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto', paddingRight: '4px' }}>
              {history.map(event => {
                const isRestart = event.event_type === 'SERVICE_RESTART';
                const isFail = event.severity === 'WARNING' || event.severity === 'ERROR';
                
                return (
                  <div key={event.id} style={{ 
                    padding: '12px', 
                    borderRadius: '8px', 
                    backgroundColor: 'rgba(255,255,255,0.01)', 
                    border: '1px solid var(--border-color)' 
                  }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)', display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: isFail ? 'var(--color-danger)' : isRestart ? 'var(--color-warning)' : 'var(--color-success)' }}>
                        {isRestart ? 'Restart Triggered' : 'Workflow Execution'}
                      </span>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px', lineHeight: '1.3' }}>
                      {event.message}
                    </div>
                  </div>
                );
              })}
              {history.length === 0 && (
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '16px', fontSize: '0.8rem' }}>
                  No historical workflow records found.
                </div>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
