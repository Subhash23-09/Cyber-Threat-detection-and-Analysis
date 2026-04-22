import { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Upload } from './components/Upload';
import { SignalView } from './components/SignalView';
import { MemoryView } from './components/MemoryView';
import { OrchestratorView } from './components/OrchestratorView';
import { AgentExecutionView } from './components/AgentExecutionView';
import { ReportingView } from './components/ReportingView';
import { LearningView } from './components/LearningView';
import { MitigationView } from './components/MitigationView';
import { NarrativeView } from './components/NarrativeView';
import { LandingPage } from './components/LandingPage';
import { Login } from './components/Login';
import { Signup } from './components/Signup';
import { Sidebar } from './components/Sidebar';
import { StatsBar } from './components/StatsBar';
import { useAuth } from './components/AuthContext';
import { Brain, ArrowRight } from 'lucide-react';
import { StreamingDashboard } from './components/StreamingDashboard';

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) return null;
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;
  return <>{children}</>;
};

// ─── Section title map ───────────────────────────────────────────
const SECTION_TITLES: Record<string, { title: string; subtitle: string }> = {
  upload:       { title: 'Universal Log Intake',     subtitle: 'Upload raw security logs for deterministic processing and AI-driven analysis.' },
  signals:      { title: 'Signal Engine Output',     subtitle: 'Raw logs converted into deterministic, explainable security signals.' },
  memory:       { title: 'Memory Retrieval',         subtitle: 'Injecting Short-Term and Long-Term context for AI reasoning.' },
  orchestrator: { title: 'LLM Orchestrator',         subtitle: 'Reasoning engine deciding the best course of action based on context.' },
  agents:       { title: 'Autonomous Agents',        subtitle: 'Specialized agents deployed to investigate and mitigate detected threats.' },
  mitigation:   { title: 'Advisory Intelligence',    subtitle: 'Actionable playbooks and remediation steps.' },
  reporting:    { title: 'Incident Reporting',       subtitle: 'Automated case file generation and archival.' },
  narrative:    { title: 'Narrative Engine',         subtitle: 'Chronological "Attack Story" weaving forensic evidence.' },
  learning:     { title: 'Learning & Memory Update', subtitle: 'Closing the loop: Assimilating intelligence.' },
};

// ─── Dashboard (sidebar layout) ─────────────────────────────────
function Dashboard({
  signals, processingStats, memory,
  showOrchestrator, activeAgents, agentReports,
  decision, isProcessing, hasProcessed,
  handleUploadComplete, handleAnalysisComplete,
  handleRunOrchestrator, handleAgentComplete,
  handleClearSession,
}: {
  signals: any[]; processingStats: any; memory: any;
  showOrchestrator: boolean; activeAgents: string[]; agentReports: Record<string, any>;
  decision: any; isProcessing: boolean; hasProcessed: boolean;
  handleUploadComplete: (_filename: string) => Promise<void>;
  handleAnalysisComplete: (_filename: string, newSignals: any[], stats: any) => Promise<void>;
  handleRunOrchestrator: () => Promise<any>;
  handleAgentComplete: (agentName: string, report: any) => void;
  handleClearSession: () => void;
}) {
  const { logout, user } = useAuth();
  const [activeTab, setActiveTab] = useState('upload');

  const hasReports = Object.keys(agentReports).length > 0;
  const criticalOrHigh = signals.filter(s =>
    s.anomaly_score === 'CRITICAL' || s.anomaly_score === 'HIGH' || s.anomaly_score === 'MEDIUM'
  ).length;
  const processingTimeMs = processingStats?.processing_time_ms ?? null;

  // Auto-advance tabs as workflow progresses
  useEffect(() => { if (hasProcessed && activeTab === 'upload') setActiveTab('signals'); }, [hasProcessed]);
  useEffect(() => { if (memory && activeTab === 'signals') setActiveTab('memory'); }, [!!memory]);
  useEffect(() => { if (showOrchestrator && activeTab === 'memory') setActiveTab('orchestrator'); }, [showOrchestrator]);
  useEffect(() => { if (activeAgents.length > 0 && activeTab === 'orchestrator') setActiveTab('agents'); }, [activeAgents.length]);
  useEffect(() => { if (hasReports && activeTab === 'agents') setActiveTab('mitigation'); }, [hasReports]);

  const section = SECTION_TITLES[activeTab] || SECTION_TITLES['upload'];

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: 'var(--bg-base)' }}>
      {/* ── Left Sidebar ── */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        hasProcessed={hasProcessed}
        hasMemory={!!memory}
        hasOrchestrator={showOrchestrator}
        hasAgents={activeAgents.length > 0}
        hasReports={hasReports}
        signalCount={signals.length}
        username={user?.username}
        onLogout={logout}
      />

      {/* ── Main Content ── */}
      <main className="flex-1 overflow-y-auto" style={{ background: 'var(--bg-base)' }}>
        {/* Top bar */}
        <div
          className="sticky top-0 z-40 px-8 py-4 flex items-center justify-between"
          style={{ background: 'var(--bg-base)', borderBottom: '1px solid var(--border-subtle)' }}
        >
          <div>
            <h2 className="text-lg font-bold font-syne" style={{ color: 'var(--text-primary)' }}>
              {section.title}
            </h2>
            <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
              {section.subtitle}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {hasProcessed && (
              <button onClick={handleClearSession} className="btn-danger text-xs">
                Clear Investigation
              </button>
            )}
          </div>
        </div>

        {/* Content area */}
        <div className="p-8">
          {/* Stats bar — shown once data exists */}
          {hasProcessed && (
            <StatsBar
              totalSignals={signals.length}
              threatsDetected={criticalOrHigh}
              processingTime={processingTimeMs}
            />
          )}

          {/* Processing spinner */}
          {isProcessing && (
            <div className="flex flex-col items-center justify-center py-20 gap-6">
              <div className="relative">
                <div className="w-16 h-16 border-4 rounded-full animate-spin"
                  style={{ borderColor: 'rgba(37,99,235,0.2)', borderTopColor: '#2563EB' }} />
                <div className="absolute inset-0 flex items-center justify-center">
                  <Brain className="w-6 h-6 animate-pulse" style={{ color: '#60A5FA' }} />
                </div>
              </div>
              <div className="text-center">
                <h3 className="text-xl font-bold font-syne" style={{ color: '#60A5FA' }}>
                  Analyzing Security Logs
                </h3>
                <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
                  Extracting signals &amp; determining threat vectors...
                </p>
              </div>
            </div>
          )}

          {/* Tab panels */}
          {!isProcessing && (
            <div>
              {/* ── Upload ── */}
              {activeTab === 'upload' && (
                <div className="card p-2 rounded-2xl">
                  <Upload
                    onUploadSuccess={handleUploadComplete}
                    onAnalysisComplete={handleAnalysisComplete}
                  />
                </div>
              )}

              {/* ── Signals ── */}
              {activeTab === 'signals' && (
                <div className="card p-6 rounded-2xl">
                  <SignalView signals={signals} stats={processingStats} />
                </div>
              )}

              {/* ── Memory ── */}
              {activeTab === 'memory' && (
                <div className="card p-6 rounded-2xl">
                  <MemoryView memory={memory} />
                </div>
              )}

              {/* ── Orchestrator ── */}
              {activeTab === 'orchestrator' && (
                <div className="card p-6 rounded-2xl">
                  <OrchestratorView onRunOrchestator={handleRunOrchestrator} />
                </div>
              )}

              {/* ── Agents ── */}
              {activeTab === 'agents' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {activeAgents.map(agent => (
                    <div key={agent} className="card p-6 rounded-2xl">
                      <AgentExecutionView
                        suggestedAgent={agent}
                        onComplete={(report) => handleAgentComplete(agent, report)}
                      />
                    </div>
                  ))}
                </div>
              )}

              {/* ── Mitigation ── */}
              {activeTab === 'mitigation' && (
                <div className="card p-6 rounded-2xl">
                  <MitigationView agentReports={agentReports} decision={decision} />
                </div>
              )}

              {/* ── Reporting ── */}
              {activeTab === 'reporting' && (
                <div className="card p-6 rounded-2xl">
                  <ReportingView agentReports={agentReports} decision={decision} />
                </div>
              )}

              {/* ── Narrative ── */}
              {activeTab === 'narrative' && (
                <div className="card p-6 rounded-2xl">
                  <NarrativeView agentReports={agentReports} decision={decision} />
                </div>
              )}

              {/* ── Learning ── */}
              {activeTab === 'learning' && (
                <div className="card p-6 rounded-2xl">
                  <LearningView caseFile={{
                    generated_at: new Date().toISOString(),
                    investigation_details: {
                      agents_deployed: activeAgents,
                      findings: Object.values(agentReports).map(r => r.report?.findings).flat(),
                      involved_trace: Array.from(new Set(signals.map(s => s.actor?.source_ip || s.source_ip).filter(Boolean))),
                      target_user: signals[0]?.target?.user || signals[0]?.target_user || 'none',
                      attack_types: Array.from(new Set(signals.map(s => s.action || s.attack_type).filter(Boolean)))
                    },
                    executive_verdict: decision
                  }} />
                </div>
              )}

              {/* ── Next step hint ── */}
              {hasProcessed && activeTab === 'upload' && (
                <div
                  className="mt-6 flex items-center gap-2 px-4 py-3 rounded-lg text-sm cursor-pointer transition-all"
                  style={{ background: 'rgba(37,99,235,0.08)', border: '1px solid rgba(37,99,235,0.2)', color: '#60A5FA' }}
                  onClick={() => setActiveTab('signals')}
                >
                  <ArrowRight className="w-4 h-4" />
                  Analysis complete — view Signal Engine Output
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

// ─── App root ────────────────────────────────────────────────────
function App() {
  const [signals, setSignals] = useState<any[]>([]);
  const [processingStats, setProcessingStats] = useState<any>(null);
  const [memory, setMemory] = useState<any>(null);
  const [showOrchestrator, setShowOrchestrator] = useState(false);
  const [activeAgents, setActiveAgents] = useState<string[]>([]);
  const [agentReports, setAgentReports] = useState<Record<string, any>>({});
  const [decision, setDecision] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [hasProcessed, setHasProcessed] = useState(false);

  const PERSISTENCE_KEY = 'acd_dashboard_state';

  useEffect(() => {
    const savedState = localStorage.getItem(PERSISTENCE_KEY);
    if (savedState) {
      try {
        const state = JSON.parse(savedState);
        if (state.signals) setSignals(state.signals);
        if (state.processingStats) setProcessingStats(state.processingStats);
        if (state.memory) setMemory(state.memory);
        if (state.showOrchestrator) setShowOrchestrator(state.showOrchestrator);
        if (state.activeAgents) setActiveAgents(state.activeAgents);
        if (state.agentReports) setAgentReports(state.agentReports);
        if (state.decision) setDecision(state.decision);
        if (state.hasProcessed) setHasProcessed(state.hasProcessed);
      } catch (e) { console.error('Failed to hydrate state', e); }
    }
  }, []);

  useEffect(() => {
    const stateToSave = { signals, processingStats, memory, showOrchestrator, activeAgents, agentReports, decision, hasProcessed };
    localStorage.setItem(PERSISTENCE_KEY, JSON.stringify(stateToSave));
  }, [signals, processingStats, memory, showOrchestrator, activeAgents, agentReports, decision, hasProcessed]);

  const handleUploadComplete = async (_filename: string) => {
    console.log(`File uploaded: ${_filename}`);
  };

  const handleAnalysisComplete = async (_filename: string, newSignals: any[], stats: any) => {
    setIsProcessing(false);
    setHasProcessed(true);
    if (stats) setProcessingStats(stats);
    if (newSignals && newSignals.length > 0) {
      setSignals(prev => [...newSignals, ...prev]);
    } else {
      try {
        const previewResp = await fetch('http://localhost:8000/api/v1/processing/signals');
        if (previewResp.ok) setSignals(await previewResp.json());
      } catch (e) { console.error('Could not fetch signal preview', e); }
    }
    try {
      const memResponse = await fetch('http://localhost:8000/api/v1/memory/context');
      if (!memResponse.ok) throw new Error();
      setMemory(await memResponse.json());
    } catch {
      setMemory({ short_term: { active_context: [], session_start: new Date().toISOString() }, long_term: { related_by_actor: [], related_by_target: [], related_by_action: [] } });
    }
    setShowOrchestrator(true);
  };

  const handleRunOrchestrator = async () => {
    const response = await fetch('http://localhost:8000/api/v1/orchestration/orchestrate', { method: 'POST' });
    const data = await response.json();
    if (data?.plan?.decision && !data.plan.decision.includes('ERROR')) {
      const decisionString = data.plan.decision;
      setDecision(data.plan);
      if (decisionString.includes('IGNORE')) {
        setActiveAgents([]);
      } else {
        const agents = decisionString.split(',').map((s: string) => {
          const agent = s.trim();
          return agent.endsWith('_AGENT') ? agent : `${agent}_AGENT`;
        });
        setActiveAgents(agents);
      }
    }
    return data;
  };

  const handleAgentComplete = (agentName: string, report: any) => {
    setAgentReports(prev => ({ ...prev, [agentName]: report }));
  };

  const handleClearSession = async () => {
    if (window.confirm('Are you sure you want to clear the current investigation and start fresh?')) {
      try {
        setSignals([]); setProcessingStats(null); setMemory(null);
        setShowOrchestrator(false); setActiveAgents([]); setAgentReports({});
        setDecision(null); setHasProcessed(false);
        localStorage.removeItem(PERSISTENCE_KEY);
        await fetch('http://localhost:8000/api/v1/processing/clear_session', { method: 'POST' });
        window.location.reload();
      } catch (e) { console.error('Failed to clear session', e); }
    }
  };

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <Dashboard
            signals={signals} processingStats={processingStats} memory={memory}
            showOrchestrator={showOrchestrator} activeAgents={activeAgents}
            agentReports={agentReports} decision={decision}
            isProcessing={isProcessing} hasProcessed={hasProcessed}
            handleUploadComplete={handleUploadComplete}
            handleAnalysisComplete={handleAnalysisComplete}
            handleRunOrchestrator={handleRunOrchestrator}
            handleAgentComplete={handleAgentComplete}
            handleClearSession={handleClearSession}
          />
        </ProtectedRoute>
      } />
      <Route path="/orchestrator" element={
        <ProtectedRoute>
          <div className="min-h-screen pt-20" style={{ background: 'var(--bg-base)' }}>
            <StreamingDashboard />
          </div>
        </ProtectedRoute>
      } />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
