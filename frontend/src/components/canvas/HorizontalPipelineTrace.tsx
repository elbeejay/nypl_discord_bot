import React, { useState } from 'react';
import {
  Cpu,
  Bot,
  Wrench,
  Layers,
  CheckCircle2,
  Loader2,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Sparkles,
} from 'lucide-react';
import type { AgentTraceStep } from '../../types/a2ui';

interface Props {
  traces?: AgentTraceStep[];
  isStreaming?: boolean;
}

export const HorizontalPipelineTrace: React.FC<Props> = ({ traces, isStreaming }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!traces || traces.length === 0) {
    return null;
  }

  const getStageIcon = (stage: string) => {
    switch (stage) {
      case 'gateway': return <Cpu size={12} />;
      case 'expert': return <Bot size={12} />;
      case 'tool': return <Wrench size={12} />;
      case 'a2ui': return <Layers size={12} />;
      default: return <Sparkles size={12} />;
    }
  };

  const completedCount = traces.filter(
    (t) => t.status === 'completed' || (!isStreaming && t.status !== 'error')
  ).length;

  return (
    <div className="canvas-pipeline-container animate-fade-in">
      {/* Streamlined Minimal Connected Ribbon */}
      <div className="canvas-pipeline-bar">
        <div className="canvas-pipeline-ribbon">
          {traces.map((step, idx) => {
            const isRunning = isStreaming && step.status === 'running';
            const isError = step.status === 'error';
            const isCompleted = !isRunning && !isError;
            const isLast = idx === traces.length - 1;

            return (
              <React.Fragment key={step.id || idx}>
                <div
                  className={`canvas-ribbon-node ${isRunning ? 'running' : isCompleted ? 'completed' : 'error'}`}
                  title={`${step.title}${step.detail ? `: ${step.detail}` : ''}`}
                >
                  <div className="canvas-ribbon-indicator">
                    {isRunning ? (
                      <Loader2 size={12} className="animate-spin text-nypl-red" />
                    ) : isError ? (
                      <AlertCircle size={12} color="var(--status-critical)" />
                    ) : (
                      <CheckCircle2 size={12} color="var(--status-success)" />
                    )}
                  </div>

                  <div className="canvas-ribbon-content">
                    <span className="canvas-ribbon-stage-icon">{getStageIcon(step.stage)}</span>
                    <span className="canvas-ribbon-title">{step.title}</span>
                  </div>
                </div>

                {!isLast && (
                  <div className={`canvas-ribbon-connector ${isCompleted ? 'completed' : isRunning ? 'active' : ''}`} />
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Action / Toggle specs */}
        <div className="canvas-pipeline-actions">
          <span className="canvas-pipeline-badge">
            {completedCount}/{traces.length} steps
          </span>
          <button
            className="canvas-pipeline-toggle"
            onClick={() => setIsExpanded(!isExpanded)}
            type="button"
            aria-expanded={isExpanded}
            title="Toggle execution details and parameters"
          >
            <span>{isExpanded ? 'Hide Specs' : 'View Specs'}</span>
            {isExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
        </div>
      </div>

      {/* Collapsible Details Drawer */}
      {isExpanded && (
        <div className="canvas-pipeline-drawer animate-fade-in">
          <div className="canvas-drawer-grid">
            {traces.map((step, idx) => (
              <div key={step.id || idx} className="canvas-drawer-card">
                <div className="canvas-drawer-card-header">
                  <span className="canvas-drawer-num">0{idx + 1}</span>
                  <span className="canvas-drawer-title">{step.title}</span>
                  <span className={`canvas-drawer-status ${step.status}`}>
                    {step.status}
                  </span>
                </div>
                {step.detail && <p className="canvas-drawer-detail">{step.detail}</p>}
                {step.tool && (
                  <div className="canvas-drawer-code">
                    <code>{step.tool}</code>
                    {step.args && <span className="canvas-drawer-args">{step.args}</span>}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
