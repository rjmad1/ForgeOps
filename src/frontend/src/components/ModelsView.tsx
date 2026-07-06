import { useEffect, useState } from 'react';
import { 
  Search, Database, Eye, Brain, Sparkles, Filter, Info 
} from 'lucide-react';
import { fetchModels } from '../services/api';
import type { Model } from '../services/api';

export default function ModelsView() {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Search & Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProvider, setSelectedProvider] = useState<string>('all');
  
  // Calculator State
  const [calcParams, setCalcParams] = useState<number>(8); // 8 Billion parameters
  const [calcQuant, setCalcQuant] = useState<number>(4); // Q4 (4-bit)

  const loadData = async () => {
    try {
      const data = await fetchModels();
      setModels(data);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch model capabilities from registry.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const formatBytes = (bytes: number | undefined): string => {
    if (!bytes || bytes === 0) return 'Unknown';
    const gb = bytes / (1024 * 1024 * 1024);
    return gb.toFixed(2) + ' GB';
  };

  // RAM/VRAM estimator
  const estimateRAM = (params: number, bits: number): number => {
    // Basic formula: (Parameters * bits) / 8 + 2GB system/context overhead
    return (params * bits) / 8 + 2;
  };

  const getProviderLogo = (provider: string) => {
    switch (provider.toLowerCase()) {
      case 'ollama': return '🦙';
      case 'litellm': return '⚡';
      case 'openclaw': return '🦞';
      case 'mcp': return '🔌';
      default: return '🤖';
    }
  };

  const filteredModels = models.filter(model => {
    const matchesSearch = model.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          model.provider.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesProvider = selectedProvider === 'all' || model.provider.toLowerCase() === selectedProvider.toLowerCase();
    return matchesSearch && matchesProvider;
  });

  const providers = Array.from(new Set(models.map(m => m.provider)));

  // Estimate capabilities from metadata/name
  const detectCapabilities = (model: Model) => {
    const name = model.name.toLowerCase();
    const isVision = name.includes('vision') || name.includes('llava') || !!model.metadata.vision;
    const isReasoning = name.includes('instruct') || name.includes('coder') || name.includes('r1') || name.includes('reasoning') || !!model.metadata.reasoning;
    const isEmbeddings = name.includes('embed') || name.includes('nomic') || model.type === 'embeddings' || !!model.metadata.embeddings;
    const isTools = name.includes('instruct') || name.includes('llama3') || name.includes('qwen') || !!model.metadata.tools;
    
    return { isVision, isReasoning, isEmbeddings, isTools };
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '16px' }}>
        <div className="spinner" />
        <p style={{ color: 'var(--text-secondary)' }}>Scanning discovered models...</p>
      </div>
    );
  }

  return (
    <div className="page-container animate-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '28px' }}>
        <div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Model Registry & Routing
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px' }}>
            Browse models discovered on local daemons and check their operational capabilities.
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
          marginBottom: '24px'
        }}>
          {error}
        </div>
      )}

      {/* Main Grid: Left is Model List, Right is RAM Estimator */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '32px', alignItems: 'start' }}>
        
        {/* Model List Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* Filters Panel */}
          <div className="card" style={{ display: 'flex', gap: '16px', padding: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ position: 'relative', flex: 1, minWidth: '200px' }}>
              <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input 
                type="text" 
                placeholder="Search models..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
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
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Filter size={14} color="var(--text-muted)" />
              <select 
                value={selectedProvider} 
                onChange={e => setSelectedProvider(e.target.value)}
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
                <option value="all">All Providers</option>
                {providers.map(p => (
                  <option key={p} value={p}>{p.toUpperCase()}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Model Cards Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '16px' }}>
            {filteredModels.map(model => {
              const caps = detectCapabilities(model);
              return (
                <div key={model.id} className="card animate-fade-in" style={{ display: 'flex', justifyContent: 'space-between', gap: '20px', padding: '20px' }}>
                  
                  {/* Left info */}
                  <div style={{ display: 'flex', gap: '16px' }}>
                    <div style={{ 
                      width: '48px', 
                      height: '48px', 
                      borderRadius: '12px', 
                      backgroundColor: 'rgba(255,255,255,0.02)', 
                      border: '1px solid var(--border-color)', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      fontSize: '1.5rem',
                      flexShrink: 0
                    }}>
                      {getProviderLogo(model.provider)}
                    </div>
                    
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <h4 style={{ fontFamily: 'var(--font-display)', fontSize: '1.05rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                          {model.name}
                        </h4>
                        <span style={{ fontSize: '0.7rem', padding: '2px 8px', backgroundColor: 'rgba(124, 58, 237, 0.08)', color: 'var(--accent-primary)', border: '1px solid rgba(124, 58, 237, 0.2)', borderRadius: '30px', fontWeight: 600 }}>
                          {model.provider}
                        </span>
                      </div>
                      
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '8px' }}>
                        <span>Family: <strong>{model.metadata.family || 'Unknown'}</strong></span>
                        <span>Size: <strong>{formatBytes(model.metadata.size_bytes)}</strong></span>
                        <span>Parameters: <strong>{model.metadata.parameter_size || 'Dynamic'}</strong></span>
                        {model.metadata.quantization_level && (
                          <span>Quant: <strong>{model.metadata.quantization_level}</strong></span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Right Capabilities badges */}
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', justifyContent: 'center', gap: '8px', minWidth: '150px' }}>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      {caps.isVision && (
                        <span title="Vision capability" style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.7rem', padding: '4px 8px', backgroundColor: 'rgba(16,185,129,0.08)', color: 'var(--color-success)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '4px', fontWeight: 600 }}>
                          <Eye size={10} /> Vision
                        </span>
                      )}
                      {caps.isTools && (
                        <span title="Supports tool-calling" style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.7rem', padding: '4px 8px', backgroundColor: 'rgba(59,130,246,0.08)', color: 'var(--color-info)', border: '1px solid rgba(59,130,246,0.2)', borderRadius: '4px', fontWeight: 600 }}>
                          🤖 Tools
                        </span>
                      )}
                      {caps.isReasoning && (
                        <span title="Reasoning/Thinking support" style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.7rem', padding: '4px 8px', backgroundColor: 'rgba(236,72,153,0.08)', color: 'var(--accent-secondary)', border: '1px solid rgba(236,72,153,0.2)', borderRadius: '4px', fontWeight: 600 }}>
                          <Brain size={10} /> Reasoning
                        </span>
                      )}
                      {caps.isEmbeddings && (
                        <span title="Embeddings provider" style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.7rem', padding: '4px 8px', backgroundColor: 'rgba(245,158,11,0.08)', color: 'var(--color-warning)', border: '1px solid rgba(245,158,11,0.2)', borderRadius: '4px', fontWeight: 600 }}>
                          <Database size={10} /> Embed
                        </span>
                      )}
                    </div>
                    
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Context Window: {model.metadata.context_window || '8,192'} tokens
                    </span>
                  </div>

                </div>
              );
            })}
            
            {filteredModels.length === 0 && (
              <div className="card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                No registered models match the filter search.
              </div>
            )}
          </div>
        </div>

        {/* RAM Estimator Column */}
        <div className="card animate-fade-in" style={{ position: 'sticky', top: '24px' }}>
          <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>
            <Sparkles size={18} color="var(--accent-primary)" />
            RAM/VRAM Estimator
          </h3>
          
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '20px', lineHeight: '1.4' }}>
            Calculate estimated workstation memory profiles for local GGUF quantizations.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Param size input */}
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Model Parameters: {calcParams}B
              </label>
              <input 
                type="range" 
                min="1" 
                max="72" 
                value={calcParams} 
                onChange={e => setCalcParams(Number(e.target.value))}
                style={{ width: '100%', marginTop: '6px', accentColor: 'var(--accent-primary)' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                <span>1B</span>
                <span>8B</span>
                <span>32B</span>
                <span>72B</span>
              </div>
            </div>

            {/* Quant level selection */}
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                Quantization Level
              </label>
              <select 
                value={calcQuant} 
                onChange={e => setCalcQuant(Number(e.target.value))}
                style={{ 
                  width: '100%',
                  padding: '8px 12px', 
                  backgroundColor: '#0b0f19', 
                  border: '1px solid var(--border-color)', 
                  borderRadius: '6px', 
                  color: 'white',
                  fontSize: '0.85rem',
                  marginTop: '6px',
                  outline: 'none'
                }}
              >
                <option value={2}>2-bit (Q2_K - Extreme compression)</option>
                <option value={3}>3-bit (Q3_K_M - Ultra compression)</option>
                <option value={4}>4-bit (Q4_K_M - Recommended standard)</option>
                <option value={5}>5-bit (Q5_K_M - High quality trade-off)</option>
                <option value={8}>8-bit (Q8_0 - Near lossless)</option>
                <option value={16}>16-bit (FP16 - Unquantized)</option>
              </select>
            </div>

            {/* Estimate Result Card */}
            <div style={{ 
              marginTop: '12px', 
              padding: '16px', 
              backgroundColor: 'rgba(0,0,0,0.15)', 
              border: '1px solid var(--border-color)', 
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Estimated VRAM Requirement
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-primary)', marginTop: '4px' }}>
                {estimateRAM(calcParams, calcQuant).toFixed(1)} GB
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'center', fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '8px' }}>
                <Info size={12} /> Includes 2GB context/system buffer
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
