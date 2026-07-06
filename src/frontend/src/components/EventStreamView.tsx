import { useEffect, useState } from 'react';
import { 
  Search, Filter, ShieldAlert, CheckCircle, AlertTriangle, 
  RefreshCw, Clock, Tag 
} from 'lucide-react';
import { fetchHistory } from '../services/api';
import type { HistoryEvent } from '../services/api';

export default function EventStreamView() {
  const [events, setEvents] = useState<HistoryEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [refreshing, setRefreshing] = useState(false);

  const loadData = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const data = await fetchHistory(100);
      setEvents(data);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch event stream from history logs.');
    } finally {
      if (showLoading) setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    // Poll events every 3 seconds
    const interval = setInterval(() => {
      loadData(false);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'ERROR': return <ShieldAlert size={14} />;
      case 'WARNING': return <AlertTriangle size={14} />;
      default: return <CheckCircle size={14} />;
    }
  };

  const filteredEvents = events.filter(e => {
    const matchesSearch = e.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          e.event_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          (e.service_id && e.service_id.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesSeverity = severityFilter === 'all' || e.severity.toUpperCase() === severityFilter.toUpperCase();
    const matchesType = typeFilter === 'all' || e.event_type.toUpperCase() === typeFilter.toUpperCase();
    
    return matchesSearch && matchesSeverity && matchesType;
  });

  const eventTypes = Array.from(new Set(events.map(e => e.event_type)));

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '16px' }}>
        <div className="spinner" />
        <p style={{ color: 'var(--text-secondary)' }}>Polling control plane history stream...</p>
      </div>
    );
  }

  return (
    <div className="page-container animate-fade-in">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px' }}>
        <div>
          <h2 style={{ fontFamily: 'var(--font-display)', fontSize: '1.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            System Event Stream
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px' }}>
            Real-time feed of control plane execution logs, health transitions, and model events.
          </p>
        </div>
        
        <button 
          onClick={handleRefresh} 
          disabled={refreshing}
          className="btn-icon"
          title="Refresh Event Feed"
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

      {/* Filter panel */}
      <div className="card" style={{ display: 'flex', gap: '16px', padding: '16px', alignItems: 'center', flexWrap: 'wrap', marginBottom: '24px' }}>
        {/* Search bar */}
        <div style={{ position: 'relative', flex: 1, minWidth: '220px' }}>
          <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input 
            type="text" 
            placeholder="Filter event description..."
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

        {/* Severity filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={14} color="var(--text-muted)" />
          <select 
            value={severityFilter} 
            onChange={e => setSeverityFilter(e.target.value)}
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
            <option value="all">All Severities</option>
            <option value="info">INFO</option>
            <option value="warning">WARNING</option>
            <option value="error">ERROR</option>
          </select>
        </div>

        {/* Event Type filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Tag size={14} color="var(--text-muted)" />
          <select 
            value={typeFilter} 
            onChange={e => setTypeFilter(e.target.value)}
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
            <option value="all">All Types</option>
            {eventTypes.map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Events List */}
      <div className="history-feed" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {filteredEvents.map(event => (
          <div key={event.id} className="history-item animate-fade-in" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <span className={`severity-indicator ${event.severity.toLowerCase()}`}>
                {getSeverityIcon(event.severity)}
              </span>
              <div>
                <div className="history-message" style={{ fontWeight: 600 }}>{event.message}</div>
                <div className="history-meta" style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '6px' }}>
                  <span className="history-tag" style={{ fontSize: '0.65rem' }}>{event.event_type}</span>
                  {event.service_id && (
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      Service: <strong>{event.service_id}</strong>
                    </span>
                  )}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
              <Clock size={12} />
              {new Date(event.timestamp).toLocaleString()}
            </div>
          </div>
        ))}

        {filteredEvents.length === 0 && (
          <div className="card" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No operational events match search filters.
          </div>
        )}
      </div>

    </div>
  );
}
