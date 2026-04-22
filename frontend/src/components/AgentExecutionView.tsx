import { Shield, AlertTriangle, Check, Play, Loader2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

interface AgentReport {
  agent: string;
  report: { verdict: 'MALICIOUS' | 'BENIGN'; findings: string[]; severity: 'LOW' | 'HIGH' | 'CRITICAL'; };
  timestamp: string;
}

interface AgentExecutionProps {
  suggestedAgent: string | null;
  onComplete?: (report: any) => void;
}

export function AgentExecutionView({ suggestedAgent, onComplete }: AgentExecutionProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [report, setReport] = useState<AgentReport | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => {
    let interval: any;
    if (isRunning) {
      setElapsedTime(0);
      interval = setInterval(() => setElapsedTime(prev => prev + 0.1), 100);
    }
    return () => clearInterval(interval);
  }, [isRunning]);

  const executeAgent = async () => {
    if (!suggestedAgent) return;
    setIsRunning(true);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/agents/${suggestedAgent}/run`, { method: 'POST' });
      const data = await response.json();
      setReport(data);
      if (onComplete) onComplete(data);
    } catch (e) { console.error(e); }
    finally { setIsRunning(false); }
  };

  if (!suggestedAgent) return null;

  const getAgentLabel = (name: string) => {
    switch (name) {
      case 'AUTH_AGENT': return 'Identity & Auth Specialist';
      case 'DDOS_AGENT': return 'Network Traffic Specialist';
      case 'EXFIL_AGENT': return 'Data Integrity Specialist';
      default: return 'General Security Agent';
    }
  };

  // NONE case
  if (suggestedAgent === 'NONE') {
    return (
      <div className="rounded-xl overflow-hidden animate-fadeInUp"
        style={{ border: '1px solid var(--border-card)', background: 'var(--bg-surface)' }}>
        <div className="flex items-center justify-between px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg" style={{ background: 'var(--bg-elevated)' }}>
              <Shield className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
            </div>
            <div>
              <h3 className="font-bold text-sm" style={{ color: 'var(--text-primary)' }}>No Active Agent Deployed</h3>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Orchestrator determined no specialized investigation is required.</p>
            </div>
          </div>
          {!report ? (
            <button onClick={() => {
              const benignReport = { agent: 'NONE', report: { verdict: 'BENIGN', findings: ['Orchestrator determined this is a false positive or low-priority event.', 'No active agent investigation was required.'], severity: 'LOW' }, timestamp: new Date().toISOString() };
              setReport(benignReport as any);
              if (onComplete) onComplete(benignReport);
            }} className="btn-ghost text-xs">
              <Check className="w-3.5 h-3.5" /> Acknowledge &amp; Continue
            </button>
          ) : (
            <div className="flex items-center gap-1 text-xs font-bold" style={{ color: '#34D399' }}>
              <Check className="w-4 h-4" /> Acknowledged
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl overflow-hidden animate-fadeInUp"
      style={{ border: '1px solid var(--border-card)', background: 'var(--bg-surface)' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4"
        style={{ borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-elevated)' }}>
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg" style={{ background: 'rgba(239,68,68,0.15)' }}>
            <Shield className="w-4 h-4" style={{ color: '#F87171' }} />
          </div>
          <div>
            <h3 className="font-bold text-sm" style={{ color: 'var(--text-primary)' }}>Active Defense Agent</h3>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{getAgentLabel(suggestedAgent)}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {isRunning && (
            <span className="font-mono text-xs animate-pulse" style={{ color: '#F87171' }}>
              T+{elapsedTime.toFixed(1)}s
            </span>
          )}
          {!report && (
            <button onClick={executeAgent} disabled={isRunning}
              className="btn-primary text-xs"
              style={{ background: isRunning ? 'rgba(239,68,68,0.5)' : '#DC2626' }}>
              {isRunning
                ? <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Deploying...</>
                : <><Play className="w-3.5 h-3.5 fill-current" /> Deploy Agent</>
              }
            </button>
          )}
          {report && (
            <span className="badge-risk" style={report.report.verdict === 'MALICIOUS'
              ? { background: 'rgba(239,68,68,0.15)', color: '#F87171', border: '1px solid rgba(239,68,68,0.3)' }
              : { background: 'rgba(16,185,129,0.15)', color: '#34D399', border: '1px solid rgba(16,185,129,0.3)' }}>
              {report.report.verdict}
            </span>
          )}
        </div>
      </div>

      {/* Terminal log while running */}
      {isRunning && (
        <div className="terminal-box m-4">
          <div style={{ color: '#34D399' }}>$ initializing {suggestedAgent.toLowerCase()}...</div>
          <div className="animate-pulse" style={{ color: 'var(--text-muted)' }}>&gt; loading context signature...</div>
          <div className="animate-pulse" style={{ color: 'var(--text-muted)' }}>&gt; verifying anomalies...</div>
        </div>
      )}

      {/* Report */}
      {report?.report && (
        <div className="p-5">
          <div className="rounded-lg overflow-hidden"
            style={{
              border: `1px solid ${report.report.verdict === 'MALICIOUS' ? 'rgba(239,68,68,0.2)' : 'rgba(16,185,129,0.2)'}`,
              background: report.report.verdict === 'MALICIOUS' ? 'rgba(239,68,68,0.04)' : 'rgba(16,185,129,0.04)',
            }}>
            <div className="px-4 py-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
              <span className="text-xs uppercase tracking-wider font-semibold" style={{ color: 'var(--text-muted)' }}>
                Investigation Report
              </span>
            </div>
            <ul className="p-4 space-y-3">
              {report.report.findings?.map((finding, idx) => (
                <li key={idx} className="flex items-start gap-3 text-sm">
                  <span className="mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0"
                    style={{ background: report.report.verdict === 'MALICIOUS' ? '#F87171' : '#34D399' }} />
                  <div className="prose prose-invert prose-sm max-w-none" style={{ color: 'var(--text-secondary)' }}>
                    <ReactMarkdown>{finding}</ReactMarkdown>
                  </div>
                </li>
              ))}
            </ul>
            {report.report.verdict === 'MALICIOUS' && (
              <div className="px-4 pb-4 flex gap-3"
                style={{ borderTop: '1px solid rgba(239,68,68,0.15)', paddingTop: '12px' }}>
                <button className="flex-1 py-2 rounded-lg text-xs font-bold transition-all"
                  style={{ background: 'rgba(239,68,68,0.12)', color: '#F87171', border: '1px solid rgba(239,68,68,0.3)' }}>
                  ISOLATE HOST
                </button>
                <button className="flex-1 py-2 rounded-lg text-xs font-bold transition-all"
                  style={{ background: 'rgba(239,68,68,0.12)', color: '#F87171', border: '1px solid rgba(239,68,68,0.3)' }}>
                  BLOCK IP
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
