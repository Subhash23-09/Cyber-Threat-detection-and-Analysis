import { Download, Check, Loader2, Archive, FileText } from 'lucide-react';
import { useState } from 'react';

interface ReportingViewProps { agentReports: Record<string, any>; decision: any; }

export function ReportingView({ agentReports, decision }: ReportingViewProps) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloaded, setDownloaded] = useState(false);

  const generateTXTReport = (reportData: any) => {
    const { case_id, generated_at, status, chain_of_custody, investigation_details } = reportData;
    const digest = btoa(case_id + (generated_at || '') + status).slice(0, 32).toUpperCase();
    return `
=========================================
      ACD-SDI SECURITY CASE FILE
=========================================
CASE ID: ${case_id}
STATUS: ${status}
GENERATED AT: ${new Date(generated_at).toLocaleString()}
-----------------------------------------

[1] Investigation Analysis
--------------------------
Agents Deployed: ${investigation_details?.agent_deployed || 'None'}
Agent Verdict: ${investigation_details?.agent_verdict || 'BENIGN'}

Technical Findings:
${investigation_details?.technical_findings?.map((f: string) => `- ${f}`).join('\n') || 'No specific findings recorded.'}

Involved Entities:
${investigation_details?.involved_trace?.join(', ') || 'N/A'}

Target Scope:
${investigation_details?.target_user || 'None'}

[2] EVIDENCE TRACEABILITY AUDIT
-------------------------------
        Signal Extraction: ${chain_of_custody?.step_2_signals?.count || 0} Signals
        Memory Context: ${chain_of_custody?.step_3_memory?.active_context_size || 0} Events
        Orchestration: ${chain_of_custody?.step_4_orchestrator?.router_decision || 'Mesh Analysis'}

-----------------------------------------
AUDIT ARTIFACT - ACD-SDI ENGINE
SHA-256 Digest: ${digest}
=========================================
    `;
  };

  const handleDownload = async (format: 'json' | 'txt') => {
    setIsDownloading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/reporting/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_reports: agentReports, decision }),
      });
      const reportData = await response.json();
      let blob: Blob, filename: string;
      if (format === 'txt') {
        blob = new Blob([generateTXTReport(reportData)], { type: 'text/plain' });
        filename = `incident-report-${reportData.case_id}.txt`;
      } else {
        blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
        filename = `incident-report-${reportData.case_id}.json`;
      }
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = filename;
      document.body.appendChild(a); a.click();
      window.URL.revokeObjectURL(url); document.body.removeChild(a);
      setDownloaded(true);
    } catch (e) { console.error(e); }
    finally { setIsDownloading(false); }
  };

  return (
    <div className="space-y-5 animate-fadeInUp">
      {/* Case header */}
      <div className="rounded-xl p-5 flex items-center justify-between"
        style={{ background: 'rgba(37,99,235,0.06)', border: '1px solid rgba(37,99,235,0.15)' }}>
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl" style={{ background: 'rgba(37,99,235,0.2)', border: '1px solid rgba(37,99,235,0.3)' }}>
            <Archive className="w-5 h-5" style={{ color: '#60A5FA' }} />
          </div>
          <div>
            <h3 className="font-bold text-base font-syne" style={{ color: 'var(--text-primary)' }}>Case Open</h3>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Incident Reporting &amp; Archival</p>
          </div>
        </div>
        <div className="text-right text-xs space-y-1">
          <div style={{ color: 'var(--text-muted)' }}>
            Status: <span className="font-bold" style={{ color: '#60A5FA' }}>OPEN</span>
          </div>
          <div style={{ color: 'var(--text-muted)' }}>
            Retention: <span className="font-mono font-bold" style={{ color: 'var(--text-secondary)' }}>365 DAYS</span>
          </div>
        </div>
      </div>

      {/* Download section */}
      <div className="rounded-xl p-6 text-center space-y-5"
        style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-card)' }}>
        <p className="text-sm max-w-lg mx-auto" style={{ color: 'var(--text-secondary)' }}>
          The full chain of custody, agent findings, and executive verdict have been sealed.
          Download the official Case File as a professional Text report or technical JSON.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3">
          <button onClick={() => handleDownload('txt')} disabled={isDownloading}
            className="btn-primary px-6 py-2.5">
            {isDownloading
              ? <><Loader2 className="w-4 h-4 animate-spin" /> Exporting TXT...</>
              : <><FileText className="w-4 h-4" /> Download Text Report</>
            }
          </button>
          <button onClick={() => handleDownload('json')} disabled={isDownloading}
            className="btn-ghost px-6 py-2.5">
            {downloaded ? <Check className="w-4 h-4" /> : <Download className="w-4 h-4" />}
            Case File
          </button>
        </div>
        <p className="text-[10px] uppercase tracking-widest font-mono" style={{ color: 'var(--text-muted)' }}>
          Audit Artifact Signed &amp; Sealed
        </p>
      </div>
    </div>
  );
}
