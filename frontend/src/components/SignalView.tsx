import { ShieldAlert, Activity, Download, ShieldCheck, Brain, Info, Filter } from 'lucide-react';
import { useState } from 'react';

interface Signal {
  id: number;
  event_type: string;
  actor: { source_ip: string; user?: string; };
  target: { user: string; destination?: string; };
  action: string;
  metrics: { failed_attempts: number; confidence: number; };
  time_window: string;
  context: { baseline?: string; asset_criticality?: string; reasoning?: string; original_detection?: string; };
  anomaly_score: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  mitre_id: string;
}

interface SignalViewProps {
  signals: Signal[];
  stats?: { total_lines: number; valid_events: number; raw_preview: string[]; };
}

const RISK_STYLES: Record<string, { border: string; badge: string; bg: string; color: string }> = {
  CRITICAL: { border: '#EF4444', badge: 'badge-risk badge-critical', bg: 'rgba(239,68,68,0.04)', color: '#F87171' },
  HIGH:     { border: '#F97316', badge: 'badge-risk badge-high',     bg: 'rgba(249,115,22,0.04)', color: '#FB923C' },
  MEDIUM:   { border: '#F59E0B', badge: 'badge-risk badge-medium',   bg: 'rgba(245,158,11,0.04)', color: '#FCD34D' },
  LOW:      { border: '#10B981', badge: 'badge-risk badge-low',      bg: 'rgba(16,185,129,0.04)', color: '#34D399' },
};

export function SignalView({ signals, stats }: SignalViewProps) {
  const [filter, setFilter] = useState<'ALL' | 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'>('ALL');
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const rawCount = stats?.total_lines || 0;
  const eventCount = stats?.valid_events || 0;
  const percentage = rawCount > 0 ? ((eventCount / rawCount) * 100).toFixed(1) : '0.0';
  const signalCount = signals.length;

  const counts = {
    ALL:      signals.length,
    CRITICAL: signals.filter(s => s.anomaly_score === 'CRITICAL').length,
    HIGH:     signals.filter(s => s.anomaly_score === 'HIGH').length,
    MEDIUM:   signals.filter(s => s.anomaly_score === 'MEDIUM').length,
    LOW:      signals.filter(s => s.anomaly_score === 'LOW').length,
  };

  const filtered = filter === 'ALL' ? signals : signals.filter(s => s.anomaly_score === filter);

  const handleDownload = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(signals, null, 2));
    const a = document.createElement('a');
    a.setAttribute('href', dataStr);
    a.setAttribute('download', 'processed_signals.json');
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  const isSemantic = (signal: Signal) => signal.event_type === 'semantic_forensic';

  return (
    <div className="space-y-5 animate-fadeInUp">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="section-icon">
            <Activity className="w-4 h-4" style={{ color: '#60A5FA' }} />
          </div>
          <div>
            <h3 className="font-bold text-base font-syne" style={{ color: 'var(--text-primary)' }}>
              Detected Signals (Step 2 Output)
            </h3>
            <div className="flex items-center gap-2 mt-0.5 text-xs font-mono" style={{ color: 'var(--text-muted)' }}>
              <span>{rawCount} Raw</span>
              <span>→</span>
              <span style={{ color: '#60A5FA' }}>{eventCount} Events ({percentage}%)</span>
              <span>→</span>
              <span style={{ color: '#A78BFA' }} className="font-bold">{signalCount} Signals</span>
            </div>
          </div>
        </div>
        <button onClick={handleDownload} className="btn-ghost text-xs">
          <Download className="w-3.5 h-3.5" /> Download JSON
        </button>
      </div>

      {/* Filter tabs */}
      <div className="flex items-center gap-1 p-1 rounded-lg" style={{ background: 'var(--bg-elevated)' }}>
        <Filter className="w-3.5 h-3.5 ml-2 flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
        {(['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map(lvl => (
          <button
            key={lvl}
            onClick={() => setFilter(lvl)}
            className="px-3 py-1.5 rounded-md text-xs font-semibold transition-all"
            style={filter === lvl
              ? { background: 'var(--bg-surface)', color: 'var(--text-primary)', boxShadow: '0 1px 4px rgba(0,0,0,0.3)' }
              : { color: 'var(--text-muted)' }
            }
          >
            {lvl} {counts[lvl] > 0 && <span className="ml-1 opacity-60">{counts[lvl]}</span>}
          </button>
        ))}
      </div>

      {/* Signal cards */}
      {filtered.length > 0 ? (
        <div className="space-y-3">
          {filtered.map(signal => {
            const rs = RISK_STYLES[signal.anomaly_score] || RISK_STYLES.LOW;
            const expanded = expandedId === signal.id;
            return (
              <div
                key={signal.id}
                className="rounded-xl overflow-hidden transition-all cursor-pointer"
                style={{
                  background: rs.bg,
                  border: `1px solid var(--border-card)`,
                  borderLeft: `4px solid ${rs.border}`,
                }}
                onClick={() => setExpandedId(expanded ? null : signal.id)}
              >
                {/* Card header */}
                <div className="flex items-center justify-between px-5 py-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg" style={{ background: isSemantic(signal) ? 'rgba(139,92,246,0.15)' : 'rgba(249,115,22,0.1)' }}>
                      {isSemantic(signal)
                        ? <Brain className="w-4 h-4" style={{ color: '#A78BFA' }} />
                        : <ShieldAlert className="w-4 h-4" style={{ color: '#FB923C' }} />
                      }
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold text-sm" style={{ color: 'var(--text-primary)' }}>{signal.action}</h4>
                        {isSemantic(signal) && (
                          <span className="text-[10px] px-2 py-0.5 rounded font-bold uppercase tracking-tight"
                            style={{ background: 'rgba(139,92,246,0.2)', color: '#C4B5FD' }}>
                            AI Reasoning
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] font-mono mt-0.5" style={{ color: 'var(--text-muted)' }}>{signal.mitre_id}</p>
                    </div>
                  </div>
                  <span className={rs.badge}>{signal.anomaly_score}</span>
                </div>

                {/* Card body */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 px-5 pb-4">
                  {[
                    { label: 'Actor (Source)', value: signal.actor.source_ip, mono: true },
                    { label: 'Target',         value: signal.target.user, mono: false },
                    { label: 'Event Count',    value: String(signal.metrics.failed_attempts || 1), mono: true },
                    { label: 'Confidence', valueEl: (
                      <div className="space-y-1">
                        <span className="font-bold text-sm" style={{ color: rs.color }}>{signal.metrics.confidence}%</span>
                        <div className="w-full h-1.5 rounded-full" style={{ background: 'var(--bg-elevated)' }}>
                          <div
                            className="h-full rounded-full transition-all"
                            style={{ width: `${signal.metrics.confidence}%`, background: rs.border }}
                          />
                        </div>
                      </div>
                    )},
                  ].map((col, i) => (
                    <div key={i}>
                      <span className="text-[10px] uppercase tracking-widest font-medium block mb-1" style={{ color: 'var(--text-muted)' }}>
                        {col.label}
                      </span>
                      {col.valueEl ? col.valueEl : (
                        <span
                          className={`text-sm ${col.mono ? 'font-mono' : 'font-medium'}`}
                          style={{ color: col.mono ? 'var(--text-secondary)' : 'var(--text-primary)' }}
                        >
                          {col.value}
                        </span>
                      )}
                    </div>
                  ))}
                </div>

                {/* Expanded reasoning */}
                {expanded && isSemantic(signal) && signal.context.reasoning && (
                  <div
                    className="px-5 py-3 flex gap-3"
                    style={{ borderTop: '1px solid rgba(139,92,246,0.12)', background: 'rgba(139,92,246,0.05)' }}
                  >
                    <Info className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: '#A78BFA' }} />
                    <p className="text-sm italic leading-relaxed" style={{ color: '#DDD6FE' }}>
                      {signal.context.reasoning}
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-16 gap-4 rounded-xl"
          style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-card)' }}
        >
          <div className="p-4 rounded-full" style={{ background: 'var(--bg-elevated)' }}>
            <ShieldCheck className="w-8 h-8" style={{ color: 'var(--text-muted)' }} />
          </div>
          <div className="text-center">
            <h4 className="font-bold" style={{ color: 'var(--text-primary)' }}>No Threat Signals Detected</h4>
            <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
              Analyzed {stats?.total_lines || 0} log entries from Step 1. No high-severity patterns matched.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
