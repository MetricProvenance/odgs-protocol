import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Terminal, ShieldCheck, Cpu, Activity, Play,
  CheckCircle, AlertTriangle, Database, Files,
  Code, Share2, ExternalLink, Search, Zap,
  ChevronRight, ArrowRight
} from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const API_BASE = "http://localhost:8000";

const SECTORS = [
  "Critical Infrastructure", "Biometrics", "Education",
  "Employment", "Essential Services", "Law Enforcement",
  "Migration", "Justice"
];

const TERMINAL_LINES = [
  "Initializing Schema Forge v2.4...",
  "Loading Protocol Definitions: [Metrics, Rules, Metadata]",
  "Connecting to Knowledge Base... OK",
  "Checking Helper Agents... OK",
  "Ready for Directive."
];

export default function App() {
  const [selectedIndustry, setSelectedIndustry] = useState(SECTORS[0]);
  const [logs, setLogs] = useState(TERMINAL_LINES);
  const [isProcessing, setIsProcessing] = useState(false);
  const [library, setLibrary] = useState([]);
  const [activeBundle, setActiveBundle] = useState(null);
  const [activeTab, setActiveTab] = useState("standard_metrics"); // metrics, rules, ontology, physical_map
  const logsEndRef = useRef(null);

  // Fetch library on mount
  useEffect(() => {
    fetchLibrary();
  }, []);

  const fetchLibrary = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/protocol/library`);
      setLibrary(res.data);
    } catch (err) {
      console.error("Failed to fetch library", err);
    }
  };

  const fetchBundle = async (industry) => {
    try {
      const res = await axios.get(`${API_BASE}/api/protocol/bundle/${industry}`);
      if (!res.data.error) {
        setActiveBundle(res.data);
        setSelectedIndustry(industry);
      }
    } catch (err) {
      console.error("Failed to fetch bundle", err);
    }
  };

  // Auto-scroll terminal
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  // Connect to SSE Stream
  useEffect(() => {
    const eventSource = new EventSource(`${API_BASE}/agent/stream`);
    eventSource.onmessage = (event) => {
      const newLog = event.data;
      if (newLog.includes("[Orchestrator]") || newLog.includes("[Schema Forge]") || newLog.includes("[System]")) {
        setLogs(prev => [...prev.slice(-19), newLog]);
        if (newLog.includes("Task Complete")) {
          setIsProcessing(false);
          fetchLibrary(); // Refresh library
          // Auto-fetch if it was the selected one
          fetchBundle(selectedIndustry);
        }
      }
    };
    return () => eventSource.close();
  }, [selectedIndustry]);

  const handleGenerate = async () => {
    setIsProcessing(true);
    setLogs(prev => [...prev, `[USER] DIRECTIVE: Generate Governance Bundle for '${selectedIndustry}'`]);
    try {
      await axios.post(`${API_BASE}/agent/generate?industry=${selectedIndustry}`);
    } catch (err) {
      console.error(err);
      setLogs(prev => [...prev, `[ERROR] Failed to contact agent: ${err.message}`]);
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#030712] text-white p-6 flex flex-col gap-6 selection:bg-cyan-500/30 font-sans">
      {/* Header */}
      <header className="flex justify-between items-center border-b border-white/5 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-cyan-500/10 rounded-lg flex items-center justify-center border border-cyan-500/30 shadow-[0_0_15px_rgba(34,211,238,0.1)]">
            <Zap className="w-5 h-5 text-cyan-400 fill-cyan-400/20" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">ODGS Governance Console</h1>
            <p className="text-slate-500 text-[10px] font-mono tracking-[0.2em] font-bold uppercase">Metric Provenance Protocol // V.2.5.0</p>
          </div>
        </div>
        <div className="flex gap-6">
          <StatusBadge label="Schema Forge" status="Standby" animate={isProcessing} />
          <StatusBadge label="Registry" status="Connected" color="emerald" />
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex gap-6 flex-1 overflow-hidden">

        {/* Left Sidebar: Protocol Library */}
        <aside className="w-72 flex flex-col gap-6">
          <Card title="Protocol Library" icon={<Files className="w-4 h-4" />} noPadding>
            <div className="flex flex-col h-full">
              <div className="p-4 border-b border-white/5">
                <div className="relative">
                  <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
                  <input
                    placeholder="Search Library..."
                    className="w-full bg-[#0a0f1d] border border-white/5 rounded-md py-2 pl-9 pr-3 text-sm text-slate-300 focus:outline-none focus:border-cyan-500/50 transition-all font-mono"
                  />
                </div>
              </div>
              <div className="flex-1 overflow-y-auto p-2 space-y-1 max-h-[400px]">
                <p className="text-[10px] text-slate-500 font-bold uppercase px-3 py-2 tracking-widest">Industry Blueprints</p>
                {library.length === 0 && <p className="text-xs text-slate-600 px-3 italic">No protocols found.</p>}
                {library.map(industry => (
                  <button
                    key={industry}
                    onClick={() => fetchBundle(industry)}
                    className={cn(
                      "w-full text-left px-3 py-2.5 rounded-md text-sm font-medium transition-all flex items-center justify-between group",
                      selectedIndustry === industry
                        ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                        : "text-slate-400 hover:bg-white/5 hover:text-white"
                    )}
                  >
                    <span className="truncate capitalize">{industry.replace(/_/g, " ")}</span>
                    <ChevronRight className={cn("w-4 h-4 transition-transform", selectedIndustry === industry ? "translate-x-0" : "-translate-x-2 opacity-0 group-hover:opacity-100 group-hover:translate-x-0")} />
                  </button>
                ))}
              </div>
            </div>
          </Card>

          <Card title="Agent Directive" icon={<Zap className="w-4 h-4 text-cyan-400" />}>
            <div className="space-y-4">
              <select
                value={selectedIndustry}
                onChange={(e) => setSelectedIndustry(e.target.value)}
                className="w-full bg-[#0a0f1d] border border-white/10 rounded-md p-3 text-sm text-white focus:outline-none focus:border-cyan-500 transition-all font-medium"
              >
                {SECTORS.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
              <button
                onClick={handleGenerate}
                disabled={isProcessing}
                className={cn(
                  "w-full py-4 rounded-lg font-bold tracking-widest uppercase transition-all flex items-center justify-center gap-3 text-sm",
                  isProcessing
                    ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-white/5"
                    : "bg-cyan-500 text-black hover:bg-cyan-400 hover:shadow-[0_0_20px_rgba(34,211,238,0.3)] shadow-lg shadow-cyan-500/20"
                )}
              >
                {isProcessing ? <Activity className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5 fill-current" />}
                {isProcessing ? "Forging..." : "Execute Agent"}
              </button>
              <div className="p-3 bg-cyan-500/5 border border-cyan-500/10 rounded-lg">
                <p className="text-[10px] text-cyan-400/80 leading-relaxed font-mono">
                  <span className="text-white font-bold">MODE:</span> NOVEL_SCHEMA_FORGE<br />
                  <span className="text-white font-bold">COMPLIANCE:</span> EU_AI_ACT_ANNEX_III
                </p>
              </div>
            </div>
          </Card>
        </aside>

        {/* Right Section: Main Terminal & Inspector */}
        <main className="flex-1 flex flex-col gap-6 h-full min-w-0">

          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 flex-1 overflow-hidden">
            {/* Live Terminal */}
            <Card title="Agent Reasoning Engine" icon={<Terminal className="w-4 h-4" />} className="flex flex-col min-h-0">
              <div className="flex-1 bg-black/40 rounded-lg p-4 font-mono text-sm overflow-y-auto border border-white/5 scrollbar-thin scrollbar-thumb-white/10">
                {logs.map((log, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -5 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="mb-1.5 flex gap-3 group"
                  >
                    <span className="text-slate-700 select-none text-xs mt-0.5">{(i + 1).toString().padStart(3, '0')}</span>
                    <LogLine text={log} />
                  </motion.div>
                ))}
                <div ref={logsEndRef} />
                {isProcessing && (
                  <motion.div
                    animate={{ opacity: [0, 1, 0] }}
                    transition={{ repeat: Infinity, duration: 0.8 }}
                    className="h-4 w-1.5 bg-cyan-500 mt-2"
                  />
                )}
              </div>
            </Card>

            {/* Protocol Inspector */}
            <Card
              title="Protocol Bundle Inspector"
              icon={<ShieldCheck className="w-4 h-4" />}
              className="flex flex-col min-h-0 relative overflow-hidden"
            >
              {activeBundle ? (
                <div className="flex flex-col h-full">
                  <div className="flex items-center justify-between mb-4 border-b border-white/5">
                    <div className="flex">
                      {["standard_metrics", "standard_data_rules", "ontology_graph", "physical_data_map"].map(tab => {
                        const hash = activeBundle.integrity?.components?.[tab]?.substring(0, 8) || "NO_FINGERPRINT";
                        return (
                          <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={cn(
                              "px-4 py-3 text-[10px] font-bold uppercase tracking-widest transition-all border-b-2 flex flex-col items-center gap-1",
                              activeTab === tab
                                ? "border-cyan-500 text-cyan-400"
                                : "border-transparent text-slate-500 hover:text-slate-300"
                            )}
                          >
                            <span>{tab.split('_').pop()}</span>
                            <span className="text-[8px] font-mono opacity-40 font-normal">{hash}</span>
                          </button>
                        );
                      })}
                    </div>
                    {activeBundle.integrity && (
                      <div className="flex items-center gap-2 px-4 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        <span className="text-[9px] font-bold text-emerald-400 font-mono">INTEGRITY_VERIFIED</span>
                      </div>
                    )}
                  </div>

                  <div className="flex-1 overflow-auto bg-[#050810] rounded-lg border border-white/5 p-4 font-mono text-[11px] leading-relaxed relative group">
                    <pre className="text-cyan-400/90 whitespace-pre-wrap">
                      {JSON.stringify(activeBundle[activeTab], null, 2)}
                    </pre>

                    {/* Floating Info */}
                    <div className="absolute top-4 right-4 flex flex-col items-end gap-2">
                      <button className="p-2 bg-white/5 hover:bg-white/10 rounded-md transition-all text-slate-400" title="Copy URN">
                        <Share2 className="w-3 h-3" />
                      </button>
                      <div className="px-2 py-1 bg-black/80 border border-white/10 rounded text-[9px] text-slate-500 font-mono hidden group-hover:block backdrop-blur-md">
                        SHA-256: {activeBundle.integrity?.components?.[activeTab]}
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 p-3 bg-white/5 rounded-lg border border-white/5 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded border border-white/10 flex items-center justify-center bg-black/20">
                        <ShieldCheck className="w-4 h-4 text-cyan-400" />
                      </div>
                      <div>
                        <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest leading-tight">Master Bundle Hash</div>
                        <div className="text-[11px] font-mono text-cyan-400/70">{activeBundle.integrity?.master_hash}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="h-4 w-px bg-white/10" />
                      <div className="text-[9px] text-slate-600 font-bold uppercase tracking-tighter">Verified by ODGS Protocol Engine</div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-slate-600 gap-4 opacity-50">
                  <div className="w-16 h-16 rounded-full border-2 border-dashed border-slate-800 flex items-center justify-center">
                    <Code className="w-8 h-8" />
                  </div>
                  <p className="text-sm font-medium">Select a protocol from the library to inspect artifacts.</p>
                </div>
              )}
            </Card>
          </div>

          {/* Impact Metrics (Billion Dollar Problem) */}
          <section className="grid grid-cols-1 md:grid-cols-4 gap-4 pb-2">
            <ImpactBadge
              label="Compliance Liability"
              value="SECURED"
              sub="Article 10 Compliant"
              icon={<ShieldCheck className="w-5 h-5 text-emerald-400" />}
            />
            <ImpactBadge
              label="Process Drift"
              value="ELIMINATED"
              sub="Single Source of Truth"
              icon={<Activity className="w-5 h-5 text-cyan-400" />}
            />
            <ImpactBadge
              label="Model Hallucination"
              value="Grounded"
              sub="RAG Context Injected"
              icon={<Cpu className="w-5 h-5 text-purple-400" />}
            />
            <ImpactBadge
              label="Market Value Shift"
              value="+ $50M"
              sub="De-risked Asset Value"
              icon={<ExternalLink className="w-5 h-5 text-orange-400" />}
            />
          </section>
        </main>
      </div>

      {/* Explainer / Footer Overlay */}
      <footer className="mt-auto pt-4 border-t border-white/5 flex justify-between items-center text-[10px] text-slate-600 font-mono tracking-widest uppercase font-bold">
        <div>© 2026 METRIC PROVENANCE // ADAPTIVE GOVERNANCE FRAMEWORK</div>
        <div className="flex gap-4">
          <span className="text-cyan-500/60 transition-colors cursor-pointer hover:text-cyan-500">Documentation</span>
          <span className="hover:text-cyan-500 transition-colors cursor-pointer">Whitepaper</span>
          <span className="hover:text-cyan-500 transition-colors cursor-pointer">Security Audit</span>
        </div>
      </footer>
    </div>
  )
}

function Card({ title, children, className, icon, noPadding = false }) {
  return (
    <div className={cn("bg-[#0a0f1d] border border-white/5 rounded-xl shadow-2xl flex flex-col", className)}>
      <div className="px-4 py-3 border-b border-white/5 flex items-center gap-2">
        {icon && <span className="opacity-50">{icon}</span>}
        <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400">{title}</h3>
      </div>
      <div className={cn("flex-1", !noPadding && "p-4")}>
        {children}
      </div>
    </div>
  )
}

function StatusBadge({ label, status, color = "cyan", animate = false }) {
  const colors = {
    cyan: "text-cyan-400 bg-cyan-400/10 border-cyan-400/20",
    emerald: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
    purple: "text-purple-400 bg-purple-400/10 border-purple-400/20"
  };

  return (
    <div className="flex items-center gap-3">
      <span className="text-[10px] text-slate-600 font-bold uppercase tracking-widest">{label}</span>
      <div className={cn("px-2 py-0.5 rounded border text-[10px] font-bold font-mono uppercase flex items-center gap-1.5", colors[color])}>
        <div className={cn("w-1.5 h-1.5 rounded-full bg-current", animate && "animate-pulse")} />
        {status}
      </div>
    </div>
  )
}

function LogLine({ text }) {
  if (text.includes("[Error]")) return <span className="text-red-400">{text}</span>;
  if (text.includes("[Schema Forge]")) return <span className="text-cyan-400">{text}</span>;
  if (text.includes("[Orchestrator]")) return <span className="text-purple-400 font-medium">{text}</span>;
  if (text.includes("[USER]")) return <span className="text-amber-400 font-bold tracking-tight">{text}</span>;
  if (text.includes("[System]")) return <span className="text-slate-500 italic">{text}</span>;
  return <span className="text-slate-300">{text}</span>;
}

function ImpactBadge({ label, value, sub, icon }) {
  return (
    <div className="bg-[#0a0f1d] border border-white/5 p-4 rounded-xl flex items-center gap-4 hover:border-cyan-500/20 transition-all group overflow-hidden relative">
      <div className="absolute top-0 right-0 p-2 opacity-10 group-hover:scale-125 transition-transform">
        {icon}
      </div>
      <div className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center shrink-0 border border-white/10 group-hover:border-cyan-500/30 transition-all">
        {icon}
      </div>
      <div>
        <div className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-0.5">{label}</div>
        <div className="text-lg font-bold text-white tracking-tight">{value}</div>
        <div className="text-[9px] text-cyan-500/60 font-mono font-bold">{sub}</div>
      </div>
    </div>
  )
}
