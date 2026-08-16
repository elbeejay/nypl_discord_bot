import React, { useState, useRef } from 'react';
import { Search, Sparkles, BookOpen, Building2, Send, History, X } from 'lucide-react';
import type { ChatMessage } from '../../types/a2ui';

interface Props {
  isLoading: boolean;
  activeCommand: string;
  onSelectCommand: (cmd: string) => void;
  onSubmitPrompt: (text: string) => void;
  inquiries: ChatMessage[];
  activeInquiryIndex: number;
  onSelectInquiry: (index: number) => void;
  onClearAll: () => void;
}

const COMMAND_MODES = [
  { id: 'ask', label: 'All / Smart Auto', icon: Sparkles, placeholder: 'Ask anything about New York City history, libraries, 311 issues, or restaurant health grades...' },
  { id: 'nypl', label: '🏛️ NYPL Archives', icon: BookOpen, placeholder: 'Ask for historic NYPL digital photographs, prints, manuscripts, or research branches...' },
  { id: 'nycdata', label: '🏙️ NYC Open Data', icon: Building2, placeholder: 'Search 311 noise complaints, restaurant health inspection scores, street trees...' },
];

export const TopCommandBar: React.FC<Props> = ({
  isLoading,
  activeCommand,
  onSelectCommand,
  onSubmitPrompt,
  inquiries,
  activeInquiryIndex,
  onSelectInquiry,
  onClearAll,
}) => {
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const activeMode = COMMAND_MODES.find((m) => m.id === activeCommand) || COMMAND_MODES[0];

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    if (!input.trim() || isLoading) return;
    onSubmitPrompt(input);
    setInput('');
  };

  return (
    <div className="canvas-top-command-container">
      {/* Top Search Bar */}
      <div className="canvas-search-box-wrapper">
        <div className="canvas-search-box">
          <div className="canvas-search-icon">
            <Search size={18} className="text-nypl-red" />
          </div>

          <input
            ref={inputRef}
            type="text"
            className="canvas-search-input"
            placeholder={activeMode.placeholder}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
          />

          <button
            className={`canvas-search-submit-btn ${input.trim() && !isLoading ? 'active' : ''}`}
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            aria-label="Submit inquiry"
          >
            {isLoading ? (
              <div className="chat-spinner" />
            ) : (
              <>
                <span>Generate Canvas</span>
                <Send size={13} />
              </>
            )}
          </button>
        </div>

        {/* Mode Selector Filters */}
        <div className="canvas-mode-filters-row">
          <div className="canvas-mode-pills">
            {COMMAND_MODES.map((mode) => {
              const Icon = mode.icon;
              const isActive = activeCommand === mode.id;
              return (
                <button
                  key={mode.id}
                  className={`canvas-mode-pill ${isActive ? 'active' : ''}`}
                  onClick={() => onSelectCommand(mode.id)}
                  type="button"
                >
                  <Icon size={12} className={isActive ? 'text-nypl-red' : ''} />
                  <span>{mode.label}</span>
                </button>
              );
            })}
          </div>

          {inquiries.length > 0 && (
            <button
              className="canvas-reset-btn"
              onClick={onClearAll}
              title="Reset Canvas & Start Fresh"
            >
              <X size={12} />
              <span>Reset Canvas</span>
            </button>
          )}
        </div>
      </div>

      {/* Inquiry History Carousel Tabs (Switch between generated dynamic canvases) */}
      {inquiries.length > 1 && (
        <div className="canvas-history-tabs-bar">
          <div className="canvas-history-label">
            <History size={12} className="text-gold" />
            <span>Research Canvases:</span>
          </div>
          <div className="canvas-history-scroll">
            {inquiries.map((inq, idx) => {
              const isActive = idx === activeInquiryIndex;
              return (
                <button
                  key={inq.id || idx}
                  className={`canvas-history-tab ${isActive ? 'active' : ''}`}
                  onClick={() => onSelectInquiry(idx)}
                >
                  <span className="canvas-history-tab-query">{inq.content}</span>
                  {inq.command && inq.command !== 'ask' && (
                    <span className="canvas-history-tab-cmd">/{inq.command}</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
