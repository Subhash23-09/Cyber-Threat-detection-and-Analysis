import { Shield, CheckCircle2, Terminal, Loader2 } from 'lucide-react';
import { useState, useEffect } from 'react';

interface Plays { title: string; actions: string[]; priority: string; }

interface MitigationViewProps {
  agentReports: Record<string, any>;
  decision: any;
  onComplete?: (playbooks: Plays[]) => void;
}

export function MitigationView({ agentReports, decision, onComplete }: MitigationViewProps) {
  const [playbooks, setPlaybooks] = useState<Plays[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (Object.keys(agentReports).length > 0) fetchPlaybooks();
  }, [agentReports]);

  const fetchPlaybooks = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/mitigation/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_reports: agentReports }),
      });
      if (response.ok) {
        const data = await response.json();
        setPlaybooks(data);
        if (onComplete) onComplete(data);
      }
    } catch (e) { console.error('Failed to fetch playbooks', e); }
    finally { setLoading(false); }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center gap-4 py-16 rounded-xl"
        style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-card)' }}>
        <Terminal className="w-10 h-10 animate-bounce" style={{ color: '#60A5FA' }} />
        <p className="text-sm uppercase tracking-widest font-mono animate-pulse" style={{ color: '#60A5FA' }}>
          Orchestrating Strategic Response...
        </p>
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Synthesizing multi-agent remediation vectors</p>
      </div>
    );
  }

  return (
    <div className="space-y-5 animate-fadeInUp">
      {/* Global strategy section */}
      {decision?.reasoning && (
        <div className="rounded-xl p-5"
          style={{ background: 'rgba(139,92,246,0.06)', border: '1px solid rgba(139,92,246,0.15)' }}>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-lg" style={{ background: 'rgba(139,92,246,0.2)' }}>
              <Terminal className="w-4 h-4" style={{ color: '#A78BFA' }} />
            </div>
            <div>
              <h3 className="font-bold text-sm font-syne" style={{ color: 'var(--text-primary)' }}>Global Autonomous Strategy</h3>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Synthesized Intelligence Layer</p>
            </div>
          </div>
          <div className="p-4 rounded-lg" style={{ background: 'var(--bg-elevated)', border: '1px solid rgba(139,92,246,0.1)' }}>
            <p className="text-sm leading-relaxed italic" style={{ color: 'var(--text-secondary)' }}>{decision.reasoning}</p>
          </div>
        </div>
      )}

      {/* Playbooks */}
      <div className="space-y-4">
        {playbooks.map((playbook, idx) => {
          const isCritical = playbook.priority.includes('CRITICAL') || playbook.priority.includes('HIGH');
          return (
            <div key={idx} className="rounded-xl overflow-hidden"
              style={{
                border: `1px solid ${isCritical ? 'rgba(239,68,68,0.2)' : 'rgba(37,99,235,0.2)'}`,
                background: isCritical ? 'rgba(239,68,68,0.04)' : 'rgba(37,99,235,0.04)',
              }}>
              <div className="flex items-center gap-3 px-5 py-4"
                style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', background: 'rgba(255,255,255,0.02)' }}>
                <div className="p-2 rounded-lg"
                  style={{ background: isCritical ? 'rgba(239,68,68,0.15)' : 'rgba(37,99,235,0.15)' }}>
                  <Shield className="w-4 h-4" style={{ color: isCritical ? '#F87171' : '#60A5FA' }} />
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-sm" style={{ color: 'var(--text-primary)' }}>{playbook.title}</h3>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded uppercase"
                      style={isCritical
                        ? { background: 'rgba(239,68,68,0.15)', color: '#F87171' }
                        : { background: 'rgba(37,99,235,0.15)', color: '#60A5FA' }}>
                      {playbook.priority}
                    </span>
                    <span className="text-[10px] uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>
                      Agent Specific Playbook
                    </span>
                  </div>
                </div>
              </div>
              <div className="p-4 space-y-2">
                {playbook.actions.map((action, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-lg transition-all"
                    style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)' }}>
                    <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5"
                      style={{ color: isCritical ? '#F87171' : '#60A5FA' }} />
                    <p className="text-sm leading-relaxed" style={{ color: 'var(--text-secondary)' }}>{action}</p>
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
