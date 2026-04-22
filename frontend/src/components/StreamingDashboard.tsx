import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Brain, Shield, Zap, Terminal, Loader2, ArrowLeft } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { useNavigate } from 'react-router-dom';

interface Event {
    type: 'thought' | 'answer';
    content: string;
}

export const StreamingDashboard: React.FC = () => {
    const navigate = useNavigate();
    const [events, setEvents] = useState<Event[]>([]);
    const [status, setStatus] = useState<'idle' | 'analyzing' | 'completed'>('idle');
    const [finalPlan, setFinalPlan] = useState<string>('');
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [events]);

    const startAnalysis = async () => {
        setEvents([]);
        setFinalPlan('');
        setStatus('analyzing');

        try {
            const response = await fetch('http://localhost:8000/api/v1/orchestration/chat_stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ trigger: 'manual' }),
            });

            if (!response.body) return;

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let accumulatedAnswer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.type === 'thought') {
                                setEvents(prev => [...prev, data]);
                            } else if (data.type === 'answer') {
                                accumulatedAnswer += data.content;
                                setFinalPlan(accumulatedAnswer);
                            }
                        } catch (e) {
                            console.error('Error parsing SSE line', e);
                        }
                    }
                }
            }
            setStatus('completed');
        } catch (err) {
            console.error('Streaming failed', err);
            setStatus('idle');
        }
    };

    return (
        <div className="max-w-6xl mx-auto p-6 space-y-6">
            <button
                onClick={() => navigate('/dashboard')}
                className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors mb-2 group"
            >
                <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                <span className="text-sm font-medium">Back to Main Dashboard</span>
            </button>
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold font-syne text-white flex items-center gap-3">
                        <Brain className="w-8 h-8 text-blue-400" />
                        Autonomous Orchestrator
                    </h2>
                    <p className="text-slate-400 mt-1">Real-time multi-agent mesh orchestration</p>
                </div>
                <button
                    onClick={startAnalysis}
                    disabled={status === 'analyzing'}
                    className="px-6 py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white rounded-xl font-bold transition-all flex items-center gap-2 shadow-lg shadow-blue-500/20"
                >
                    {status === 'analyzing' ? <Loader2 className="w-5 h-5 animate-spin" /> : <Zap className="w-5 h-5" />}
                    {status === 'analyzing' ? 'Orchestrating...' : 'Initialize Defense Mesh'}
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Thought Process Panel */}
                <div className="lg:col-span-1 glass rounded-2xl border-white/5 flex flex-col h-[600px]">
                    <div className="p-4 border-b border-white/5 flex items-center gap-2 bg-white/5">
                        <Terminal className="w-4 h-4 text-blue-400" />
                        <span className="text-sm font-bold uppercase tracking-wider">Thought Process</span>
                    </div>
                    <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
                        <AnimatePresence>
                            {events.map((event, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    className="flex gap-3"
                                >
                                    <div className="mt-1">
                                        <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                                    </div>
                                    <p className="text-sm text-slate-300 leading-relaxed font-mono">
                                        {event.content}
                                    </p>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                        {status === 'analyzing' && (
                            <div className="flex items-center gap-2 text-slate-500 text-xs font-mono animate-pulse">
                                <span>&gt;</span>
                                <span className="w-2 h-4 bg-slate-500" />
                            </div>
                        )}
                    </div>
                </div>

                {/* Main Answer / Plan Panel */}
                <div className="lg:col-span-2 glass rounded-2xl border-white/5 flex flex-col h-[600px] overflow-hidden">
                    <div className="p-4 border-b border-white/5 flex items-center gap-2 bg-blue-500/10">
                        <Shield className="w-4 h-4 text-blue-400" />
                        <span className="text-sm font-bold uppercase tracking-wider">Defense Infrastructure Plan</span>
                    </div>
                    <div className="flex-1 overflow-y-auto p-8 prose prose-invert max-w-none">
                        {finalPlan ? (
                            <div className="markdown-content">
                                <ReactMarkdown>
                                    {finalPlan}
                                </ReactMarkdown>
                            </div>
                        ) : (
                            <div className="h-full flex flex-col items-center justify-center text-slate-500 space-y-4">
                                <Brain className="w-12 h-12 opacity-20" />
                                <p>Waiting for orchestrator synthesis...</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
