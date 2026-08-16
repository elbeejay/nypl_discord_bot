import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Copy, Check, BookOpen, Building2, Sparkles, Compass } from 'lucide-react';
import type { ChatMessage } from '../../types/a2ui';

interface Props {
  userQuery?: string;
  responseMessage: ChatMessage;
}

export const EditorialSummaryCard: React.FC<Props> = ({ userQuery, responseMessage }) => {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(responseMessage.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getDomainBadge = () => {
    const cmd = responseMessage.command || 'ask';
    if (cmd === 'nypl') {
      return (
        <div className="canvas-domain-tag tag-nypl">
          <BookOpen size={12} />
          <span>NYPL Digital Collections</span>
        </div>
      );
    }
    if (cmd === 'nycdata') {
      return (
        <div className="canvas-domain-tag tag-nyc">
          <Building2 size={12} />
          <span>NYC Open Data</span>
        </div>
      );
    }
    return (
      <div className="canvas-domain-tag tag-auto">
        <Sparkles size={12} />
        <span>Multi-Agent Synthesis</span>
      </div>
    );
  };

  return (
    <div className="canvas-editorial-card animate-fade-in">
      {/* Editorial Card Header */}
      <div className="canvas-editorial-header">
        <div className="canvas-editorial-headline-wrapper">
          {getDomainBadge()}
          {userQuery && (
            <h2 className="canvas-editorial-query-title serif-heading">
              {userQuery}
            </h2>
          )}
        </div>

        <button
          className="canvas-copy-btn"
          onClick={copyToClipboard}
          title="Copy finding summary"
          aria-label="Copy summary"
        >
          {copied ? <Check size={14} color="#10B981" /> : <Copy size={14} />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>

      {/* Editorial Body Text */}
      <div className="canvas-editorial-body">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            a: ({ node, ...props }) => (
              <a {...props} target="_blank" rel="noopener noreferrer" />
            ),
            table: ({ node, ...props }) => (
              <div style={{ overflowX: 'auto', margin: '14px 0' }}>
                <table className="a2ui-table" {...props} />
              </div>
            ),
          }}
        >
          {responseMessage.content || 'Analyzing request and preparing synthesized findings...'}
        </ReactMarkdown>
      </div>

      {/* Editorial Footer */}
      <div className="canvas-editorial-footer">
        <div className="canvas-footer-brand">
          <Compass size={13} className="text-nypl-red" />
          <span>NYPL Research Engine · Generated via Gemini 3.5 Flash Lite Multi-Agent Architecture</span>
        </div>
        <span className="canvas-timestamp">
          {new Date(responseMessage.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
};
