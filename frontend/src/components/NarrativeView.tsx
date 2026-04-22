import { BookOpen, Loader2, Sparkles, Quote } from 'lucide-react';
import { useState } from 'react';

interface NarrativeViewProps { agentReports: Record<string, any>; decision: any; }

export function NarrativeView({ agentReports, decision }: NarrativeViewProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [narrative, setNarrative] = useState('');
  const [hasRun, setHasRun] = useState(false);

  const generateNarrative = async () => {
    setIsRunning(true);
    setNarrative('');
    setHasRun(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/narrative/storylines', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_reports: agentReports, decision }),
      });
      if (!response.body) return;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      while (!done) {
        const { value, done: isDone } = await reader.read();
        done = isDone;
        if (value) setNarrative(prev => prev + decoder.decode(value, { stream: true }));
      }
    } catch (e) { console.error('Narrative generation failed', e); }
    finally { setIsRunning(false); }
  };

  return (
    <div className="space-y-5 animate-fadeInUp">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="section-icon" style={{ background: 'rgba(16,185,129,0.15)' }}>
            <BookOpen className="w-4 h-4" style={{ color: '#34D399' }} />
          </div>
          <div>
            <h3 className="font-bold text-base font-syne" style={{ color: 'var(--text-primary)' }}>Attack Narrative</h3>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Step 9: Storyline Engine</p>
          </div>
        </div>
        {!hasRun && !isRunning && (
          <button onClick={generateNarrative}
            className="btn-primary"
            style={{ background: 'linear-gradient(135deg, #059669, #10B981)', boxShadow: '0 4px 16px rgba(16,185,129,0.25)' }}>
            <Sparkles className="w-4 h-4" /> Generate Story
          </button>
        )}
      </div>

      {/* Loading */}
      {isRunning && (
        <div className="flex items-center gap-3 p-4 rounded-lg animate-pulse"
          style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.15)' }}>
          <Loader2 className="w-4 h-4 animate-spin" style={{ color: '#34D399' }} />
          <span className="text-sm font-mono uppercase tracking-widest" style={{ color: '#34D399' }}>
            Weaving telemetry into narrative...
          </span>
        </div>
      )}

      {/* Narrative text */}
      {narrative && (
        <div className="relative rounded-xl p-6"
          style={{ background: 'var(--bg-surface)', border: '1px solid rgba(16,185,129,0.12)' }}>
          <div className="absolute -left-1 top-4 opacity-10">
            <Quote className="w-10 h-10 rotate-180" style={{ color: '#34D399' }} />
          </div>
          <div className="pl-6 space-y-5 font-serif">
            {narrative.split('\n\n').map((paragraph, i) => (
              <p key={i} className="text-base leading-relaxed"
                style={{ color: 'var(--text-secondary)' }}>
                {paragraph}
              </p>
            ))}
          </div>
          <div className="absolute -right-1 bottom-4 opacity-10">
            <Quote className="w-10 h-10" style={{ color: '#34D399' }} />
          </div>
        </div>
      )}
    </div>
  );
}
