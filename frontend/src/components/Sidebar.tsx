import {
  Upload, Activity, Brain, GitBranch, Shield, ClipboardList,
  FileText, BookOpen, RefreshCw, LogOut, ShieldCheck, ChevronRight
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  hasProcessed: boolean;
  hasMemory: boolean;
  hasOrchestrator: boolean;
  hasAgents: boolean;
  hasReports: boolean;
  signalCount?: number;
  username?: string;
  onLogout: () => void;
}

const navItems = [
  { id: 'upload',      label: 'Universal Log Intake',      icon: Upload,        alwaysOn: true },
  { id: 'signals',     label: 'Signal Engine Output',      icon: Activity,      requiresProcessed: true },
  { id: 'memory',      label: 'Memory Retrieval',          icon: Brain,         requiresMemory: true },
  { id: 'orchestrator',label: 'LLM Orchestrator',          icon: GitBranch,     requiresOrchestrator: true },
  { id: 'agents',      label: 'Autonomous Agents',         icon: Shield,        requiresAgents: true },
  { id: 'mitigation',  label: 'Advisory Intelligence',     icon: ClipboardList, requiresReports: true },
  { id: 'reporting',   label: 'Incident Reporting',        icon: FileText,      requiresReports: true },
  { id: 'narrative',   label: 'Narrative Engine',          icon: BookOpen,      requiresReports: true },
  { id: 'learning',    label: 'Learning & Memory Update',  icon: RefreshCw,     requiresReports: true },
];

export function Sidebar({
  activeTab, setActiveTab,
  hasProcessed, hasMemory, hasOrchestrator, hasAgents, hasReports,
  signalCount, username, onLogout
}: SidebarProps) {

  const isEnabled = (item: typeof navItems[0]) => {
    if (item.alwaysOn) return true;
    if (item.requiresProcessed && !hasProcessed) return false;
    if (item.requiresMemory && !hasMemory) return false;
    if (item.requiresOrchestrator && !hasOrchestrator) return false;
    if (item.requiresAgents && !hasAgents) return false;
    if (item.requiresReports && !hasReports) return false;
    return true;
  };

  return (
    <aside
      className="flex flex-col h-screen sticky top-0"
      style={{
        width: 240,
        minWidth: 240,
        background: 'var(--bg-sidebar)',
        borderRight: '1px solid var(--border-subtle)',
        boxShadow: '2px 0 20px rgba(0,0,0,0.3)',
      }}
    >
      {/* Logo */}
      <div className="p-5 border-b" style={{ borderColor: 'var(--border-subtle)' }}>
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg" style={{ background: 'rgba(37,99,235,0.2)' }}>
            <ShieldCheck className="w-5 h-5" style={{ color: '#60A5FA' }} />
          </div>
          <div>
            <p className="font-bold text-sm font-syne tracking-tight" style={{ color: 'var(--text-primary)' }}>
              ACD-SDI Platform
            </p>
            <p className="text-[10px]" style={{ color: 'var(--text-muted)' }}>
              Verified Session
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
        {navItems.map(item => {
          const enabled = isEnabled(item);
          const active = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => enabled && setActiveTab(item.id)}
              disabled={!enabled}
              className={`sidebar-item w-full text-left ${active ? 'active' : ''} ${!enabled ? 'opacity-30 cursor-not-allowed' : 'cursor-pointer'}`}
            >
              <item.icon className="w-4 h-4 flex-shrink-0" />
              <span className="flex-1 text-sm">{item.label}</span>
              {item.id === 'signals' && signalCount && signalCount > 0 ? (
                <span
                  className="text-[10px] font-bold px-1.5 py-0.5 rounded-full"
                  style={{ background: 'rgba(37,99,235,0.25)', color: '#60A5FA' }}
                >
                  {signalCount}
                </span>
              ) : null}
              {active && <ChevronRight className="w-3 h-3 opacity-50 flex-shrink-0" />}
            </button>
          );
        })}
      </nav>

      {/* User footer */}
      <div className="p-3 border-t" style={{ borderColor: 'var(--border-subtle)' }}>
        <div className="flex items-center justify-between px-2 py-2 rounded-lg" style={{ background: 'var(--bg-elevated)' }}>
          <div className="flex items-center gap-2 min-w-0">
            <div
              className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
              style={{ background: 'rgba(37,99,235,0.3)', color: '#60A5FA' }}
            >
              {username ? username[0].toUpperCase() : 'U'}
            </div>
            <span className="text-xs font-medium truncate" style={{ color: 'var(--text-secondary)' }}>
              {username || 'Analyst'}
            </span>
          </div>
          <button
            onClick={onLogout}
            className="p-1.5 rounded-md transition-all flex-shrink-0"
            style={{ color: 'var(--text-muted)' }}
            onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.color = '#EF4444'; (e.currentTarget as HTMLButtonElement).style.background = 'rgba(239,68,68,0.1)'; }}
            onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-muted)'; (e.currentTarget as HTMLButtonElement).style.background = 'transparent'; }}
            title="Disconnect"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
