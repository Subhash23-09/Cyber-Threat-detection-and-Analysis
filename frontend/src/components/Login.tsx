import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Shield, Mail, Lock, ArrowRight, Loader2, AlertCircle, Zap, Database } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from './AuthContext';

export const Login: React.FC = () => {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier, password }),
      });
      const data = await response.json();
      if (response.ok) { login(data.token, data.user); navigate('/dashboard'); }
      else setError(data.error || 'Invalid credentials');
    } catch { setError('Failed to connect to authentication server'); }
    finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen flex" style={{ background: 'var(--bg-base)' }}>
      {/* Left branding panel */}
      <div className="hidden lg:flex flex-col justify-between w-[420px] flex-shrink-0 p-10"
        style={{ background: 'var(--bg-sidebar)', borderRight: '1px solid var(--border-subtle)' }}>
        <div>
          <div className="flex items-center gap-2.5 mb-12">
            <div className="p-1.5 rounded-lg" style={{ background: 'rgba(37,99,235,0.2)' }}>
              <Shield className="w-5 h-5" style={{ color: '#60A5FA' }} />
            </div>
            <span className="font-bold font-syne tracking-tight" style={{ color: 'var(--text-primary)' }}>ACD-SDI Platform</span>
          </div>
          <h2 className="text-2xl font-bold font-syne mb-4" style={{ color: 'var(--text-primary)' }}>
            An AI-Orchestrated Multi-Agent Framework for Cyber Threat Analysis
          </h2>
          <p className="text-sm leading-relaxed mb-10" style={{ color: 'var(--text-muted)' }}>
            Empower your SOC with self-healing infrastructure. Identifies, analyzes, and provides mitigations to threats before they impact your business.
          </p>
          <div className="space-y-4">
            {[
              { icon: Zap, label: 'Real-time Analysis', desc: 'Sub-millisecond signal extraction' },
              { icon: Database, label: 'Universal Ingest', desc: 'Any source: AWS, Azure, On-prem' },
              { icon: Shield, label: 'Self-Healing', desc: 'Autonomous agents for mitigation' },
            ].map((f, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="p-1.5 rounded-lg flex-shrink-0" style={{ background: 'rgba(37,99,235,0.12)' }}>
                  <f.icon className="w-3.5 h-3.5" style={{ color: '#60A5FA' }} />
                </div>
                <div>
                  <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{f.label}</p>
                  <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>© 2025 Autonomous Cyber Defense</p>
      </div>

      {/* Right form panel */}
      <div className="flex-1 flex items-center justify-center px-6 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full blur-[100px]"
            style={{ background: 'rgba(37,99,235,0.06)' }} />
        </div>
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-sm relative">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold font-syne" style={{ color: 'var(--text-primary)' }}>Welcome Back</h1>
            <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>Access your defense intelligence</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
                className="p-3 rounded-lg flex items-center gap-2 text-sm"
                style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#F87171' }}>
                <AlertCircle className="w-4 h-4 flex-shrink-0" /> {error}
              </motion.div>
            )}
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: 'var(--text-muted)' }} />
              <input type="text" placeholder="Username or Email" className="form-input pl-10"
                value={identifier} onChange={e => setIdentifier(e.target.value)} required />
            </div>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style={{ color: 'var(--text-muted)' }} />
              <input type="password" placeholder="Password" className="form-input pl-10"
                value={password} onChange={e => setPassword(e.target.value)} required />
            </div>
            <button type="submit" disabled={loading}
              className="w-full py-3 rounded-lg font-bold text-sm text-white transition-all flex items-center justify-center gap-2"
              style={{ background: loading ? 'rgba(37,99,235,0.5)' : 'var(--accent-blue)', boxShadow: '0 4px 16px rgba(37,99,235,0.25)' }}>
              {loading
                ? <Loader2 className="w-4 h-4 animate-spin" />
                : <><span>Login</span><ArrowRight className="w-4 h-4" /></>
              }
            </button>
          </form>

          <p className="mt-6 text-center text-sm" style={{ color: 'var(--text-muted)' }}>
            New User?{' '}
            <Link to="/signup" className="font-bold" style={{ color: '#60A5FA' }}>Signup</Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
};
