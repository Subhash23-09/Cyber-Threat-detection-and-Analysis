import { BookOpen, Check, Database, Loader2, AlertTriangle } from 'lucide-react';
import { useState } from 'react';

export function LearningView({ caseFile }: { caseFile: any }) {
  const [isLearning, setIsLearning] = useState(false);
  const [learnResult, setLearnResult] = useState<any>(null);

  const handleLearn = async () => {
    setIsLearning(true);
    console.log('DEBUG: Sending case_file to /learn:', caseFile);
    try {
      const response = await fetch('http://localhost:8000/api/v1/narrative/learn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_file: caseFile }),
      });
      const data = await response.json();
      setLearnResult(data);
    } catch (e) { console.error(e); }
    finally { setIsLearning(false); }
  };

  if (!caseFile) return null;

  const trace = caseFile.investigation_details.involved_trace || [];
  const types = caseFile.investigation_details.attack_types || [];
  const count = (trace.length || 0) + (types.length || 0) + 1;

  return (
    <div className="space-y-5 animate-fadeInUp">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="section-icon" style={{ background: 'rgba(139,92,246,0.15)' }}>
            <BookOpen className="w-4 h-4" style={{ color: '#A78BFA' }} />
          </div>
          <div>
            <h3 className="font-bold text-base font-syne" style={{ color: 'var(--text-primary)' }}>Knowledge Base Update</h3>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Reinforcement Learning from Human Feedback (RLHF)</p>
          </div>
        </div>
        {!learnResult && (
          <button onClick={handleLearn} disabled={isLearning}
            className="btn-primary"
            style={{ background: isLearning ? 'rgba(139,92,246,0.4)' : '#7C3AED' }}>
            {isLearning
              ? <><Loader2 className="w-4 h-4 animate-spin" /> Indexing {count} fragments...</>
              : <><Database className="w-4 h-4" /> Update Memory ({count})</>
            }
          </button>
        )}
      </div>

      {/* Info box */}
      <div className="p-4 rounded-lg text-sm"
        style={{ background: 'rgba(139,92,246,0.06)', border: '1px solid rgba(139,92,246,0.12)', color: 'var(--text-secondary)' }}>
        By confirming this incident, you are updating the system's Long-Term Memory.
        Future log analysis will compare against this unique signature to speed up detection.
      </div>

      {/* Result */}
      {learnResult && (
        <div className="rounded-lg p-5 animate-fadeInUp"
          style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-card)' }}>
          {learnResult.status === 'error' ? (
            <div className="flex items-center gap-3" style={{ color: '#F87171' }}>
              <AlertTriangle className="w-5 h-5" />
              <span className="font-bold">Error Updating Memory: {learnResult.message}</span>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-3 mb-3" style={{ color: '#34D399' }}>
                <Check className="w-5 h-5" />
                <span className="font-bold">Knowledge Base Updated Successfully</span>
              </div>
              <div className="ml-8 text-sm" style={{ color: 'var(--text-muted)' }}>
                <p>
                  Total confirmed cases of this type:{' '}
                  <span className="font-mono font-bold" style={{ color: 'var(--text-primary)' }}>
                    {learnResult.total_related_cases}
                  </span>
                </p>
                <p className="mt-1">
                  The system is now better equipped to handle{' '}
                  <b style={{ color: 'var(--text-secondary)' }}>{caseFile.investigation_details.agent_deployed}</b> attacks.
                </p>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
