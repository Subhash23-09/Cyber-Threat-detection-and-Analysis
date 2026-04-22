import { GitBranch, BrainCircuit, Loader2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';

interface OrchestratorResult {
  status: string;
  message?: string;
  context_analyzed?: number;
  plan?: { decision: string; reasoning: string; confidence: string; };
}

interface OrchestratorViewProps {
  onRunOrchestator: () => Promise<OrchestratorResult>;
  isAutoTriggered?: boolean;
}

export function OrchestratorView({ onRunOrchestator, isAutoTriggered }: OrchestratorViewProps) {
  const navigate = useNavigate();
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<OrchestratorResult | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => { if (isAutoTriggered) handleRun(); }, [isAutoTriggered]);

  useEffect(() => {
    let interval: any;
    if (isRunning) {
      setElapsedTime(0);
      interval = setInterval(() => setElapsedTime(prev => prev + 0.1), 100);
    }
    return () => clearInterval(interval);
  }, [isRunning]);

  const handleRun = async () => {
    setIsRunning(true);
    try { const res = await onRunOrchestator(); setResult(res); }
    catch (e) { console.error(e); }
    finally { setIsRunning(false); }
  };

  const isPositiveDecision = result?.plan?.decision && !result.plan.decision.includes('ERROR') && result.plan.decision !== 'IGNORE';

  return (
    <div className="space-y-5 animate-fadeInUp">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="section-icon">
            <BrainCircuit className="w-4 h-4" style={{ color: '#22D3EE' }} />
          </div>
          <div>
            <h3 className="font-bold text-base font-syne" style={{ color: 'var(--text-primary)' }}>LLM Orchestrator</h3>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Reasoning Engine (Llama 3 70b)</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isRunning && (
            <span className="font-mono text-sm animate-pulse" style={{ color: '#22D3EE' }}>
              T+{elapsedTime.toFixed(1)}s
            </span>
          )}
          {!result && (
            <>
              <button
                onClick={() => navigate('/orchestrator')}
                className="btn-ghost text-xs"
              >
                <BrainCircuit className="w-3.5 h-3.5" /> Open Mesh Stream
              </button>
              <button
                onClick={handleRun}
                disabled={isRunning}
                className="btn-primary"
                style={isRunning ? { opacity: 0.6 } : {}}
              >
                {isRunning
                  ? <><Loader2 className="w-4 h-4 animate-spin" /> Reasoning...</>
                  : <><GitBranch className="w-4 h-4" /> Run Orchestrator</>
                }
              </button>
            </>
          )}
        </div>
      </div>

      {/* Loading state */}
      {isRunning && (
        <div className="rounded-xl p-6 space-y-3" style={{ background: 'var(--bg-surface)', border: '1px solid rgba(34,211,238,0.1)' }}>
          {['Reading Memory Context...', 'Analyzing 0-shot patterns...', 'Formulating Agent Plan...'].map((step, i) => (
            <div key={i} className="flex items-center gap-3 text-sm" style={{ color: `rgba(34,211,238,${1 - i * 0.3})` }}>
              <Loader2 className="w-4 h-4 animate-spin flex-shrink-0" />
              {step}
            </div>
          ))}
        </div>
      )}

      {/* Result */}
      {result?.plan && (
        <div className="rounded-xl overflow-hidden animate-fadeInUp"
          style={{ border: '1px solid var(--border-card)', background: 'var(--bg-surface)' }}>
          <div className="px-5 py-4 flex items-center justify-between"
            style={{ borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-elevated)' }}>
            <span className="text-xs uppercase tracking-wider font-semibold" style={{ color: 'var(--text-muted)' }}>
              Decision Output
            </span>
            <div className="flex items-center gap-3">
              <div>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Action</p>
                <span className="text-lg font-bold font-mono" style={{ color: isPositiveDecision ? '#34D399' : '#F87171' }}>
                  {result.plan.decision}
                </span>
              </div>
              <div className="px-3 py-1.5 rounded-lg text-xs font-bold"
                style={{ background: 'rgba(34,211,238,0.12)', color: '#22D3EE', border: '1px solid rgba(34,211,238,0.2)' }}>
                {result.plan.confidence}
              </div>
            </div>
          </div>
          <div className="px-5 py-4">
            <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>Reasoning</p>
            <div className="prose prose-invert prose-sm max-w-none" style={{ color: 'var(--text-secondary)' }}>
              <ReactMarkdown>{result.plan.reasoning}</ReactMarkdown>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
