import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Cpu,
  Bot,
  Wrench,
  Layers,
  CheckCircle2,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import type { AgentTraceStep } from '../../types/a2ui';

interface Props {
  traces?: AgentTraceStep[];
  isStreaming?: boolean;
}

export const AgentTraceViewer: React.FC<Props> = ({ traces, isStreaming }) => {
  // Show pipeline trace expanded by default
  const [isExpanded, setIsExpanded] = useState(true);

  if (!traces || traces.length === 0) {
    return null;
  }

  const getStageIcon = (stage: string) => {
    switch (stage) {
      case 'gateway': return <Cpu size={13} className="text-nypl-red" />;
      case 'expert': return <Bot size={13} className="text-nypl-red" />;
      case 'tool': return <Wrench size={13} className="text-nypl-red" />;
      case 'a2ui': return <Layers size={13} className="text-nypl-red" />;
      default: return <CheckCircle2 size={13} color="#10B981" />;
    }
  };

  const activeStep = traces[traces.length - 1];

  return (
    <div className="agent-trace-container animate-fade-in">
      {/* Header Summary Bar */}
      <button
        className="agent-trace-header"
        onClick={() => setIsExpanded(!isExpanded)}
        type="button"
        aria-expanded={isExpanded}
      >
        <div className="agent-trace-summary">
          <div className="agent-trace-pulsing-dot-wrapper">
            {isStreaming ? (
              <Loader2 size={13} className="animate-spin text-nypl-red" />
            ) : (
              <div className="agent-trace-status-dot-done" />
            )}
          </div>

          <span className="agent-trace-title">
            {isStreaming
              ? (activeStep?.detail || activeStep?.title || 'Agent Orchestration in Progress...')
              : `Multi-Agent Pipeline Executed (${traces.length} step${traces.length === 1 ? '' : 's'})`}
          </span>
        </div>

        <div className="agent-trace-toggle-icon">
          <span className="agent-trace-toggle-text">{isExpanded ? 'Hide Trace' : 'Show Trace'}</span>
          {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </div>
      </button>

      {/* Expanded Node Stepper Graph */}
      {isExpanded && (
        <div className="agent-trace-pipeline animate-fade-in">
          <div className="agent-trace-nodes-list">
            {traces.map((step, idx) => {
              const isRunning = isStreaming && step.status === 'running';
              const isError = step.status === 'error';
              const isCompleted = !isRunning && !isError;
              const isLast = idx === traces.length - 1;

              return (
                <div
                  key={step.id || idx}
                  className={`agent-trace-node ${isRunning ? 'node-running' : isCompleted ? 'node-completed' : 'node-error'}`}
                >
                  {/* Connector Line */}
                  {!isLast && <div className="agent-trace-line" />}

                  {/* Status Indicator Circle */}
                  <div className={`agent-trace-icon-circle ${isRunning ? 'running' : isError ? 'error' : 'done'}`}>
                    {isRunning ? (
                      <Loader2 size={12} className="animate-spin text-nypl-red" />
                    ) : isError ? (
                      <AlertCircle size={12} color="#EF4444" />
                    ) : (
                      <CheckCircle2 size={12} color="#10B981" />
                    )}
                  </div>

                  {/* Node Content */}
                  <div className="agent-trace-content">
                    <div className="agent-trace-node-header">
                      <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        {getStageIcon(step.stage)}
                        <span className="agent-trace-node-title">{step.title}</span>
                      </div>
                      {step.agent && <span className="agent-trace-tag">{step.agent}</span>}
                    </div>

                    {step.detail && (
                      <p className="agent-trace-detail">{step.detail}</p>
                    )}

                    {step.tool && (
                      <div className="agent-trace-tool-badge">
                        <code>{step.tool}</code>
                        {step.args && <span className="agent-trace-args">({step.args})</span>}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
