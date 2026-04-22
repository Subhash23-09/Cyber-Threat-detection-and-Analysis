import React from 'react';
import { motion } from 'framer-motion';
import { Shield, Zap, Lock, Database, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen text-white selection:bg-blue-500/30 overflow-x-hidden"
      style={{ background: 'var(--bg-base)' }}>
      {/* Background decorative glows */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full blur-[120px] animate-glow"
          style={{ background: 'rgba(37,99,235,0.08)' }} />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full blur-[120px] animate-glow"
          style={{ background: 'rgba(139,92,246,0.08)', animationDelay: '2s' }} />
        <div className="absolute inset-0 bg-grid opacity-[0.03]" />
      </div>

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50"
        style={{ background: 'rgba(14,20,32,0.85)', backdropFilter: 'blur(12px)', borderBottom: '1px solid var(--border-subtle)' }}>
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg" style={{ background: 'rgba(37,99,235,0.2)' }}>
              <Shield className="w-5 h-5" style={{ color: '#60A5FA' }} />
            </div>
            <span className="text-base font-extrabold tracking-tighter uppercase font-syne">ACD-SDI</span>
          </div>
          <div className="hidden md:flex items-center gap-6 text-sm font-medium">
            <a href="#features" className="transition-colors" style={{ color: 'var(--text-muted)' }}
              onMouseEnter={e => (e.currentTarget as HTMLAnchorElement).style.color = '#60A5FA'}
              onMouseLeave={e => (e.currentTarget as HTMLAnchorElement).style.color = 'var(--text-muted)'}>
              Features
            </a>
            <Link to="/login"
              className="px-4 py-2 rounded-lg text-sm font-medium transition-all"
              style={{ color: 'var(--text-secondary)', border: '1px solid var(--border-subtle)' }}>
              Log In
            </Link>
            <Link to="/signup"
              className="px-4 py-2 rounded-lg text-sm font-medium transition-all text-white"
              style={{ background: 'var(--accent-blue)', boxShadow: '0 4px 12px rgba(37,99,235,0.3)' }}>
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative pt-36 pb-20 px-6">
        <div className="max-w-5xl mx-auto text-center relative z-10">
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
            <span className="inline-block px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest mb-6"
              style={{ background: 'rgba(37,99,235,0.1)', border: '1px solid rgba(37,99,235,0.2)', color: '#60A5FA' }}>
              Next-Gen Cybersecurity
            </span>
            <h1 className="text-4xl md:text-6xl font-black mb-6 leading-[1.1] font-syne tracking-tighter">
              An AI-Orchestrated Multi-Agent Framework{' '}
              <br />
              <span style={{ background: 'linear-gradient(135deg, #60A5FA, #818CF8, #A78BFA)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                for Log-Centric Cyber Threat Analysis
              </span>
            </h1>
            <p className="max-w-xl mx-auto text-base mb-10 leading-relaxed" style={{ color: 'var(--text-muted)' }}>
              Empower your SOC with self-healing infrastructure. Our AI-driven platform identifies, analyzes, and provide mitigations to threats before they impact your business.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/signup"
                className="group flex items-center gap-2 px-8 py-3.5 rounded-xl text-base font-bold text-white transition-all"
                style={{ background: 'var(--accent-blue)', boxShadow: '0 8px 24px rgba(37,99,235,0.3)' }}>
                Try Now
                <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
              </Link>
              <Link to="/login"
                className="flex items-center gap-2 px-8 py-3.5 rounded-xl text-base font-bold transition-all"
                style={{ color: 'var(--text-secondary)', border: '1px solid var(--border-card)' }}>
                View Demo
              </Link>
            </div>
          </motion.div>

          {/* Hero image */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, delay: 0.4 }}
            className="mt-20 relative">
            <div className="absolute inset-0 rounded-2xl blur-[60px]"
              style={{ background: 'rgba(37,99,235,0.12)' }} />
            <div className="relative rounded-2xl overflow-hidden"
              style={{ border: '1px solid var(--border-card)', background: 'var(--bg-surface)' }}>
              <img src="/frontend_image.jpg" alt="Cyber Threat Analysis Dashboard"
                className="w-full h-auto opacity-90" />
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="relative py-20 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-extrabold mb-4 font-syne">Intelligence Driven Protection</h2>
            <p className="text-sm max-w-lg mx-auto" style={{ color: 'var(--text-muted)' }}>
              Built by security experts, powered by the latest breakthroughs in large language models.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-5">
            {[
              { icon: Zap, title: 'Real-time Analysis', desc: 'Process millions of logs per second with sub-millisecond signal extraction.', color: '#60A5FA', bg: 'rgba(37,99,235,0.12)' },
              { icon: Database, title: 'Universal Ingest', desc: 'Aggregate logs from any source: AWS, Azure, On-prem, or Custom applications.', color: '#A78BFA', bg: 'rgba(139,92,246,0.12)' },
              { icon: Lock, title: 'Self-Healing', desc: 'Autonomous agents that verify and provide mitigations to mitigate threats.', color: '#34D399', bg: 'rgba(16,185,129,0.12)' },
            ].map((f, i) => (
              <motion.div key={i} whileHover={{ y: -6 }}
                className="p-6 rounded-xl transition-all group"
                style={{ background: 'var(--bg-surface)', border: '1px solid var(--border-card)' }}
                onMouseEnter={e => (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(37,99,235,0.3)'}
                onMouseLeave={e => (e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border-card)'}>
                <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-4" style={{ background: f.bg }}>
                  <f.icon className="w-5 h-5" style={{ color: f.color }} />
                </div>
                <h3 className="text-lg font-bold mb-2 font-syne">{f.title}</h3>
                <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative py-10 px-6" style={{ borderTop: '1px solid var(--border-subtle)' }}>
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4" style={{ color: '#60A5FA' }} />
            <span className="text-sm font-bold font-syne tracking-tighter uppercase">ACD-SDI</span>
          </div>
          <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
            © 2025 Autonomous Cyber Defense. Built for the future of security.
          </div>
        </div>
      </footer>
    </div>
  );
};
