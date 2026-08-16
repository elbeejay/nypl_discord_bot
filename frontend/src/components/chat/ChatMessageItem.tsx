import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Copy, Check, User, Loader2 } from 'lucide-react';
import type { ChatMessage } from '../../types/a2ui';
import { A2UIRenderer } from '../a2ui/A2UIRenderer';
import { AgentTraceViewer } from './AgentTraceViewer';

interface Props {
  message: ChatMessage;
  onActionClick?: (prompt: string) => void;
}

export const ChatMessageItem: React.FC<Props> = ({ message, onActionClick }) => {
  const [copied, setCopied] = useState(false);
  const isModel = message.role === 'model';

  const copyToClipboard = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getCommandBadge = () => {
    if (!message.command || message.command === 'ask') return null;
    return (
      <span className="nypl-command-badge">
        /{message.command}
      </span>
    );
  };

  return (
    <div className={`chat-message-row ${isModel ? 'message-model' : 'message-user'} animate-fade-in`}>
      <div className="chat-avatar-container">
        {isModel ? (
          <div className="chat-avatar avatar-model" title="NYPL & NYC Agent">
            <span role="img" aria-label="NYPL Lion" style={{ fontSize: '18px' }}>🦁</span>
          </div>
        ) : (
          <div className="chat-avatar avatar-user" title="You">
            <User size={16} color="#FFFFFF" />
          </div>
        )}
      </div>

      <div className="chat-message-body">
        <div className="chat-message-header">
          <span className="chat-sender-name">
            {isModel ? 'NYPL Urban Agent' : 'You'}
          </span>
          {getCommandBadge()}
          <span className="chat-timestamp">
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>

          {isModel && message.content && (
            <button
              className="chat-copy-btn"
              onClick={copyToClipboard}
              title="Copy message to clipboard"
            >
              {copied ? <Check size={13} color="#10B981" /> : <Copy size={13} />}
            </button>
          )}
        </div>

        {/* Live Visual Agent-to-Agent (A2A) Reasoning & Tool Pipeline */}
        {isModel && message.traces && message.traces.length > 0 && (
          <AgentTraceViewer
            traces={message.traces}
            isStreaming={message.isStreaming}
          />
        )}

        {/* Live Agent Reasoning / Tool Calling Status Indicator */}
        {message.statusMessage && (!message.traces || message.traces.length === 0) && (
          <div className="chat-status-pill animate-fade-in">
            <Loader2 size={13} className="animate-spin text-nypl-red" />
            <span>{message.statusMessage}</span>
          </div>
        )}

        {/* Text Content with Markdown */}
        {message.content && (
          <div className="chat-markdown-content">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                a: ({ node, ...props }) => (
                  <a {...props} target="_blank" rel="noopener noreferrer" />
                ),
                table: ({ node, ...props }) => (
                  <div style={{ overflowX: 'auto', margin: '12px 0' }}>
                    <table className="a2ui-table" {...props} />
                  </div>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}

        {/* Dynamic A2UI Visualizations (Charts, Maps, Lightbox, Tables) */}
        {message.a2ui && (
          <A2UIRenderer
            payload={message.a2ui}
            onActionClick={onActionClick}
          />
        )}
      </div>
    </div>
  );
};
