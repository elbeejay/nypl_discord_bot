import React, { useState } from 'react';
import {
  Sparkles,
  ArrowRight,
  Cpu,
  Layers,
  ShieldCheck,
  Code2,
  BookOpen,
  Building2,
  MapPin,
  BarChart3,
  Image as ImageIcon,
  Table,
  CheckCircle2,
  Bot
} from 'lucide-react';

interface Props {
  onSelectPrompt: (prompt: string, command: string) => void;
  onBackToCanvas: () => void;
}

export const ArchitectureExplainer: React.FC<Props> = ({
  onSelectPrompt,
  onBackToCanvas,
}) => {
  const [copiedStep, setCopiedStep] = useState<string | null>(null);

  const sampleExtensibilityCode = `# 1. Define the tool (async Python function)
async def query_subway_alerts(line: str) -> str:
    """Look up real-time MTA subway delays & alerts."""
    return await mta_client.get_alerts(line)

# 2. Define the specialized expert agent
transit_agent = genai.Client().aio.chats.create(
    model=settings.EXPERT_MODEL,
    config=types.GenerateContentConfig(
        system_instruction="You are the MTA Transit Specialist...",
        tools=[query_subway_alerts]
    )
)

# 3. Register tool with Gateway Orchestrator
async def delegate_to_transit_agent(query: str) -> str:
    return await transit_agent.send_message(query)`;

  const copyCode = () => {
    navigator.clipboard.writeText(sampleExtensibilityCode);
    setCopiedStep('copied');
    setTimeout(() => setCopiedStep(null), 2000);
  };

  return (
    <div className="explainer-container animate-fade-in">
      {/* Top Banner / Pitch Header */}
      <div className="explainer-hero-card">
        <div className="explainer-hero-badge">
          <Sparkles size={14} className="text-nypl-red animate-pulse-glow" />
          <span>Hackathon System Architecture & 30-Second Pitch</span>
        </div>

        <div className="explainer-hero-header">
          <div>
            <h2 className="explainer-hero-title serif-heading">
              NYC & NYPL Multi-Agent Intelligence Engine
            </h2>
            <p className="explainer-hero-subtitle">
              Engineered with <strong>Gemini 3.5 Flash Lite</strong>, declarative <strong>Agent-to-User Interface (A2UI)</strong> widgets, and a single unified <strong>FastAPI</strong> backend.
            </p>
          </div>

          <button className="a2ui-btn-primary explainer-action-btn" onClick={onBackToCanvas}>
            <span>Try Live Canvas</span>
            <ArrowRight size={14} />
          </button>
        </div>

        {/* At-a-Glance 5-Second Pipeline Strip */}
        <div className="explainer-pipeline-strip">
          <div className="pipeline-node">
            <span className="node-icon">📱</span>
            <div className="node-text">
              <strong>Dual Ingress</strong>
              <small>Discord Bot + Web SPA</small>
            </div>
          </div>
          <span className="pipeline-arrow">➔</span>

          <div className="pipeline-node highlight">
            <span className="node-icon">🧠</span>
            <div className="node-text">
              <strong>Gateway Router</strong>
              <small>Gemini 3.5 Flash Lite Triage</small>
            </div>
          </div>
          <span className="pipeline-arrow">➔</span>

          <div className="pipeline-node">
            <span className="node-icon">🏛️🏙️</span>
            <div className="node-text">
              <strong>Domain Experts</strong>
              <small>NYPL Digital + NYC SODA</small>
            </div>
          </div>
          <span className="pipeline-arrow">➔</span>

          <div className="pipeline-node highlight-gold">
            <span className="node-icon">🎨</span>
            <div className="node-text">
              <strong>Generative A2UI</strong>
              <small>Interactive Visual Cards</small>
            </div>
          </div>
        </div>
      </div>

      {/* 4 Core Pillars (2x2 Grid) */}
      <div className="explainer-grid">
        {/* Pillar 1: Multi-Agent Hierarchy */}
        <div className="explainer-card">
          <div className="explainer-card-header">
            <div className="explainer-icon-badge">
              <Cpu size={18} className="text-nypl-red" />
            </div>
            <div>
              <h3 className="explainer-card-title">1. Multi-Agent Hierarchy (A2A)</h3>
              <p className="explainer-card-sub">Specialized delegation beats monolithic prompts</p>
            </div>
          </div>

          <div className="explainer-card-body">
            <p className="explainer-text">
              Instead of an overloaded single prompt, our <strong>Gateway Orchestrator</strong> routes intent to specialized expert agents and synthesizes cross-domain findings:
            </p>
            <div className="explainer-pill-list">
              <div className="explainer-pill">
                <BookOpen size={13} className="text-nypl-red" />
                <span><strong>NYPL Archives Specialist:</strong> Digital repository & branch locator</span>
              </div>
              <div className="explainer-pill">
                <Building2 size={13} className="text-nypl-red" />
                <span><strong>NYC Open Data Specialist:</strong> SoQL queries on 311, health grades, & trees</span>
              </div>
              <div className="explainer-pill">
                <Bot size={13} className="text-gold" />
                <span><strong>Cross-Domain Synthesis:</strong> Joins historical context with live city data</span>
              </div>
            </div>
          </div>
        </div>

        {/* Pillar 2: Declarative A2UI Widgets */}
        <div className="explainer-card">
          <div className="explainer-card-header">
            <div className="explainer-icon-badge">
              <Layers size={18} className="text-nypl-red" />
            </div>
            <div>
              <h3 className="explainer-card-title">2. Generative A2UI Protocol</h3>
              <p className="explainer-card-sub">Structured declarative visual components on the fly</p>
            </div>
          </div>

          <div className="explainer-card-body">
            <p className="explainer-text">
              Our AI doesn't just return plain text—it emits typed <strong>A2UI JSON schemas</strong> rendered into responsive, interactive frontend widgets:
            </p>
            <div className="explainer-widgets-grid">
              <div className="widget-chip"><MapPin size={12} className="text-nypl-red" /> Geo Leaflet Maps</div>
              <div className="widget-chip"><BarChart3 size={12} className="text-blue" /> Chart.js Graphs</div>
              <div className="widget-chip"><ImageIcon size={12} className="text-gold" /> NYPL Photo Lightboxes</div>
              <div className="widget-chip"><Table size={12} className="text-green" /> CSV-Export Data Grids</div>
            </div>
            <div className="catalog-link-row">
              <span className="status-indicator-dot" />
              <span>Live Schema Discovery Endpoint: <code>/api/v1/a2ui/catalog</code></span>
            </div>
          </div>
        </div>

        {/* Pillar 3: 10-Line Backend Extensibility */}
        <div className="explainer-card">
          <div className="explainer-card-header">
            <div className="explainer-icon-badge">
              <Code2 size={18} className="text-nypl-red" />
            </div>
            <div>
              <h3 className="explainer-card-title">3. Plug & Play Extensibility</h3>
              <p className="explainer-card-sub">Add new civic agents in less than 10 lines of code</p>
            </div>
          </div>

          <div className="explainer-card-body">
            <div className="code-snippet-header">
              <span>Adding an MTA Transit Specialist:</span>
              <button className="code-copy-btn" onClick={copyCode}>
                {copiedStep === 'copied' ? <CheckCircle2 size={12} color="#10B981" /> : <Code2 size={12} />}
                <span>{copiedStep === 'copied' ? 'Copied' : 'Copy Blueprint'}</span>
              </button>
            </div>
            <pre className="code-snippet-box">
              <code>{sampleExtensibilityCode}</code>
            </pre>
          </div>
        </div>

        {/* Pillar 4: Dual-Channel & Enterprise Posture */}
        <div className="explainer-card">
          <div className="explainer-card-header">
            <div className="explainer-icon-badge">
              <ShieldCheck size={18} className="text-nypl-red" />
            </div>
            <div>
              <h3 className="explainer-card-title">4. Production & Dual-Channel Parity</h3>
              <p className="explainer-card-sub">One backend powering both Discord & Web</p>
            </div>
          </div>

          <div className="explainer-card-body">
            <ul className="explainer-feature-list">
              <li>
                <CheckCircle2 size={13} className="text-green" />
                <span><strong>Discord Webhook Security:</strong> Constant-time Ed25519 signatures with 300s replay validation.</span>
              </li>
              <li>
                <CheckCircle2 size={13} className="text-green" />
                <span><strong>Tamper-Proof Sessions:</strong> HMAC-SHA256 HttpOnly cookies with sliding-window rate limiting.</span>
              </li>
              <li>
                <CheckCircle2 size={13} className="text-green" />
                <span><strong>Real-time Telemetry:</strong> SSE streaming with live step-by-step reasoning trace progression.</span>
              </li>
              <li>
                <CheckCircle2 size={13} className="text-green" />
                <span><strong>Container Hardening:</strong> Multi-stage non-root container deployment on GCP Cloud Run.</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Quick Launch Demo Queries */}
      <div className="explainer-footer-cta">
        <div className="cta-left">
          <Sparkles size={16} className="text-nypl-red" />
          <div>
            <strong>Ready to Test in Action?</strong>
            <p>Click any sample query to switch immediately to the interactive canvas:</p>
          </div>
        </div>

        <div className="cta-buttons-row">
          <button
            className="a2ui-action-chip"
            onClick={() => {
              onSelectPrompt('Search NYPL digital archives for historical Brooklyn Bridge construction photographs', 'nypl');
              onBackToCanvas();
            }}
          >
            <span>🏛️ NYPL Brooklyn Bridge Archives</span>
          </button>

          <button
            className="a2ui-action-chip"
            onClick={() => {
              onSelectPrompt('What are recent 311 noise complaints in Astoria Queens with location and status?', 'nycdata');
              onBackToCanvas();
            }}
          >
            <span>🏙️ 311 Noise in Astoria</span>
          </button>

          <button
            className="a2ui-action-chip"
            onClick={() => {
              onSelectPrompt('Tell me about the historic Schwarzman building and find 311 complaints near 42nd St', 'ask');
              onBackToCanvas();
            }}
          >
            <span>✨ Cross-Domain Synthesis</span>
          </button>
        </div>
      </div>
    </div>
  );
};
