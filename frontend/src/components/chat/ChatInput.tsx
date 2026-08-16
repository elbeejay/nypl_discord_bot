import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, BookOpen, Building2 } from 'lucide-react';

interface Props {
  isLoading: boolean;
  activeCommand: string;
  onSelectCommand: (cmd: string) => void;
  onSendMessage: (text: string) => void;
}

const COMMAND_OPTIONS = [
  { id: 'ask', label: 'All / Smart Auto', icon: Sparkles, desc: 'Auto-orchestrates between NYPL & NYC Open Data' },
  { id: 'nypl', label: '🏛️ NYPL Archives', icon: BookOpen, desc: 'Historical photos, manuscripts & research collections' },
  { id: 'nycdata', label: '🏙️ NYC Open Data', icon: Building2, desc: '311 complaints, restaurant grades & street trees' },
];

export const ChatInput: React.FC<Props> = ({
  isLoading,
  activeCommand,
  onSelectCommand,
  onSendMessage,
}) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [input]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    if (!input.trim() || isLoading) return;
    onSendMessage(input);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  return (
    <div className="chat-input-wrapper">
      {/* Command Selector Tabs */}
      <div className="chat-command-tabs">
        {COMMAND_OPTIONS.map((cmd) => {
          const Icon = cmd.icon;
          const isActive = activeCommand === cmd.id;
          return (
            <button
              key={cmd.id}
              className={`chat-command-tab ${isActive ? 'active' : ''}`}
              onClick={() => onSelectCommand(cmd.id)}
              type="button"
              title={cmd.desc}
            >
              <Icon size={13} className={isActive ? 'text-nypl-red' : ''} />
              <span>{cmd.label}</span>
            </button>
          );
        })}
      </div>

      {/* Main Input Box */}
      <div className="chat-input-box">
        <textarea
          ref={textareaRef}
          className="chat-textarea"
          placeholder={
            activeCommand === 'nypl'
              ? 'Ask about historic NYPL digital photos, maps, manuscripts, or branches...'
              : activeCommand === 'nycdata'
              ? 'Ask about NYC 311 noise complaints, restaurant inspection grades, street trees...'
              : 'Ask anything about New York City history, libraries, or civic data...'
          }
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          rows={1}
        />

        <button
          className={`chat-send-btn ${input.trim() && !isLoading ? 'active' : ''}`}
          onClick={handleSend}
          disabled={!input.trim() || isLoading}
          aria-label="Send message"
        >
          {isLoading ? (
            <div className="chat-spinner" />
          ) : (
            <Send size={16} />
          )}
        </button>
      </div>

      <div className="chat-input-footer">
        <span>Press <kbd>Enter ↵</kbd> to send, <kbd>Shift + Enter</kbd> for newline</span>
        <span className="chat-input-brand">NYC & NYPL A2UI Engine</span>
      </div>
    </div>
  );
};
