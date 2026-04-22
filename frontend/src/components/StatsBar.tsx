import { Activity, ShieldAlert, Clock } from 'lucide-react';

interface StatsBarProps {
  totalSignals: number;
  threatsDetected: number;
  processingTime?: number | null; // in milliseconds
}

export function StatsBar({ totalSignals, threatsDetected, processingTime }: StatsBarProps) {
  const formatTime = (ms: number | null | undefined) => {
    if (!ms && ms !== 0) return '—';
    return `${ms.toFixed(0)} ms`;
  };

  const stats = [
    {
      label: 'Total Signals',
      value: totalSignals.toLocaleString(),
      icon: Activity,
      color: '#60A5FA',
      bg: 'rgba(37,99,235,0.12)',
    },
    {
      label: 'Threats Detected',
      value: threatsDetected.toLocaleString(),
      icon: ShieldAlert,
      color: '#F87171',
      bg: 'rgba(239,68,68,0.12)',
    },
    {
      label: 'Processing Time',
      value: formatTime(processingTime),
      icon: Clock,
      color: '#34D399',
      bg: 'rgba(16,185,129,0.12)',
    },
  ];

  return (
    <div className="flex items-stretch gap-4 mb-6">
      {stats.map((stat, i) => (
        <div key={i} className="stats-card flex-1">
          <div
            className="p-2 rounded-lg flex-shrink-0"
            style={{ background: stat.bg }}
          >
            <stat.icon className="w-4 h-4" style={{ color: stat.color }} />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
              {stat.label}
            </p>
            <p className="text-xl font-bold font-inter mt-0.5" style={{ color: 'var(--text-primary)' }}>
              {stat.value}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
