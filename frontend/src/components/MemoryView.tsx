import { Database, Zap, User, Target, Crosshair } from 'lucide-react';

interface MemoryContext {
  short_term: { session_start: string; active_context: any[]; };
  long_term: { related_by_actor: any[]; related_by_target: any[]; related_by_action: any[]; };
}

export function MemoryView({ memory }: { memory: MemoryContext | null }) {
  if (!memory) return null;

  const totalLongTerm =
    (memory.long_term?.related_by_actor?.length || 0) +
    (memory.long_term?.related_by_target?.length || 0) +
    (memory.long_term?.related_by_action?.length || 0);

  return (
    <div className="grid md:grid-cols-2 gap-5 animate-fadeInUp">
      {/* Short-Term Memory */}
      <div className="rounded-xl overflow-hidden" style={{ border: '1px solid rgba(96,165,250,0.15)', background: 'rgba(37,99,235,0.04)' }}>
        <div className="flex items-center gap-3 px-5 py-4" style={{ borderBottom: '1px solid rgba(96,165,250,0.1)', background: 'rgba(37,99,235,0.06)' }}>
          <div className="p-1.5 rounded-lg" style={{ background: 'rgba(37,99,235,0.2)' }}>
            <Zap className="w-4 h-4" style={{ color: '#60A5FA' }} />
          </div>
          <div>
            <h3 className="font-bold text-sm" style={{ color: 'var(--text-primary)' }}>Short-Term Memory</h3>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Active Session Context</p>
          </div>
          <span className="ml-auto text-xs font-mono px-2 py-0.5 rounded"
            style={{ background: 'rgba(37,99,235,0.15)', color: '#93C5FD' }}>
            {memory.short_term.active_context.length} items
          </span>
        </div>
        <div className="p-5 space-y-2">
          {memory.short_term.active_context.length === 0 ? (
            <p className="text-sm italic" style={{ color: 'var(--text-muted)' }}>No active signals in memory.</p>
          ) : (
            memory.short_term.active_context.slice(-3).map((item, idx) => (
              <div key={idx} className="p-3 rounded-lg" style={{ background: 'var(--bg-elevated)', border: '1px solid rgba(96,165,250,0.08)' }}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium" style={{ color: '#93C5FD' }}>
                    {item.action || item.suspected_attack}
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded font-bold"
                    style={{ background: 'rgba(37,99,235,0.2)', color: '#60A5FA' }}>
                    {item.anomaly_score}
                  </span>
                </div>
                <p className="text-xs font-mono" style={{ color: 'var(--text-muted)' }}>
                  {item.actor?.source_ip || item.source_ip} → {item.target?.user || item.target_user}
                </p>
              </div>
            ))
          )}
          {memory.short_term.active_context.length > 3 && (
            <p className="text-xs text-center pt-1" style={{ color: 'var(--text-muted)' }}>
              + {memory.short_term.active_context.length - 3} more active items
            </p>
          )}
        </div>
      </div>

      {/* Long-Term Memory */}
      <div className="rounded-xl overflow-hidden" style={{ border: '1px solid rgba(167,139,250,0.15)', background: 'rgba(139,92,246,0.04)' }}>
        <div className="flex items-center gap-3 px-5 py-4" style={{ borderBottom: '1px solid rgba(167,139,250,0.1)', background: 'rgba(139,92,246,0.06)' }}>
          <div className="p-1.5 rounded-lg" style={{ background: 'rgba(139,92,246,0.2)' }}>
            <Database className="w-4 h-4" style={{ color: '#A78BFA' }} />
          </div>
          <div>
            <h3 className="font-bold text-sm" style={{ color: 'var(--text-primary)' }}>Long-Term Memory</h3>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>6-Factor Historical Context</p>
          </div>
          <span className="ml-auto text-xs font-mono px-2 py-0.5 rounded"
            style={{ background: 'rgba(139,92,246,0.15)', color: '#C4B5FD' }}>
            {totalLongTerm} related
          </span>
        </div>
        <div className="p-5 space-y-4">
          {totalLongTerm === 0 ? (
            <p className="text-sm italic" style={{ color: 'var(--text-muted)' }}>No historical correlations found.</p>
          ) : (
            <>
              {memory.long_term.related_by_actor?.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <User className="w-3 h-3" style={{ color: '#A78BFA' }} />
                    <span className="text-xs font-semibold" style={{ color: '#A78BFA' }}>
                      By Actor ({memory.long_term.related_by_actor.length})
                    </span>
                  </div>
                  {memory.long_term.related_by_actor.slice(0, 2).map((item, idx) => (
                    <div key={idx} className="p-2.5 rounded-lg mb-1.5 text-xs"
                      style={{ background: 'var(--bg-elevated)', border: '1px solid rgba(167,139,250,0.08)' }}>
                      <span className="font-mono" style={{ color: '#C4B5FD' }}>{item.actor?.source_ip || item.source_ip}</span>
                      <span className="ml-2" style={{ color: 'var(--text-muted)' }}>• {item.action || item.suspected_attack}</span>
                    </div>
                  ))}
                </div>
              )}
              {memory.long_term.related_by_target?.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <Target className="w-3 h-3" style={{ color: '#A78BFA' }} />
                    <span className="text-xs font-semibold" style={{ color: '#A78BFA' }}>
                      By Target ({memory.long_term.related_by_target.length})
                    </span>
                  </div>
                  {memory.long_term.related_by_target.slice(0, 2).map((item, idx) => (
                    <div key={idx} className="p-2.5 rounded-lg mb-1.5 text-xs"
                      style={{ background: 'var(--bg-elevated)', border: '1px solid rgba(167,139,250,0.08)' }}>
                      <span className="font-mono" style={{ color: '#C4B5FD' }}>{item.target?.user || item.target_user}</span>
                      <span className="ml-2" style={{ color: 'var(--text-muted)' }}>• {item.action || item.suspected_attack}</span>
                    </div>
                  ))}
                </div>
              )}
              {memory.long_term.related_by_action?.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 mb-2">
                    <Crosshair className="w-3 h-3" style={{ color: '#A78BFA' }} />
                    <span className="text-xs font-semibold" style={{ color: '#A78BFA' }}>
                      By Action ({memory.long_term.related_by_action.length})
                    </span>
                  </div>
                  {memory.long_term.related_by_action.slice(0, 2).map((item, idx) => (
                    <div key={idx} className="p-2.5 rounded-lg mb-1.5 text-xs"
                      style={{ background: 'var(--bg-elevated)', border: '1px solid rgba(167,139,250,0.08)' }}>
                      <span className="font-semibold" style={{ color: '#C4B5FD' }}>{item.action || item.suspected_attack}</span>
                      <span className="ml-2 text-[10px]" style={{ color: 'var(--text-muted)' }}>
                        {new Date(item.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
