import { Sun, Moon, Plus, KeyRound, Lock, Sparkles, Cpu } from 'lucide-react';

interface Props {
  theme?: 'light' | 'dark';
  onToggleTheme?: () => void;
  onGoHome?: () => void;
  onResetChat?: () => void;
  messageCount?: number;
  isAuthenticated?: boolean;
  onOpenKeyModal?: () => void;
  onLogout?: () => void;
  activeView?: 'canvas' | 'explainer';
  onSelectView?: (view: 'canvas' | 'explainer') => void;
}

export const Header: React.FC<Props> = ({
  theme = 'light',
  onToggleTheme,
  onGoHome,
  onResetChat,
  messageCount = 0,
  isAuthenticated = false,
  onOpenKeyModal,
  onLogout,
  activeView = 'canvas',
  onSelectView,
}) => {
  const handleReset = onGoHome || onResetChat || (() => {});

  return (
    <header className="nypl-header">
      {/* Top Brand Bar */}
      <div className="nypl-header-inner">
        {/* Clickable Brand / Logo to return to Home Screen */}
        <div
          className="nypl-header-brand"
          onClick={() => {
            if (onSelectView) onSelectView('canvas');
            handleReset();
          }}
          role="button"
          tabIndex={0}
          title="Return to Home / Start New Inquiry"
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              if (onSelectView) onSelectView('canvas');
              handleReset();
            }
          }}
        >
          <div className="nypl-lion-badge">
            <span role="img" aria-label="NYPL Lion" style={{ fontSize: '24px' }}>🦁</span>
          </div>
          <div>
            <div className="nypl-title-row">
              <h1 className="nypl-site-title serif-heading">The New York Public Library</h1>
              <span className="nypl-tag-pill">Dynamic A2UI Canvas</span>
            </div>
            <p className="nypl-site-sub">Digital Collections Archive & NYC Urban Intelligence</p>
          </div>
        </div>

        {/* View Switcher Pill Navigation */}
        {onSelectView && (
          <div className="nypl-view-toggle" role="tablist" aria-label="View Mode">
            <button
              className={`nypl-view-tab ${activeView === 'canvas' ? 'active' : ''}`}
              onClick={() => onSelectView('canvas')}
              role="tab"
              aria-selected={activeView === 'canvas'}
            >
              <Sparkles size={13} />
              <span>Canvas</span>
            </button>
            <button
              className={`nypl-view-tab ${activeView === 'explainer' ? 'active' : ''}`}
              onClick={() => onSelectView('explainer')}
              role="tab"
              aria-selected={activeView === 'explainer'}
            >
              <Cpu size={13} />
              <span>30s Pitch & Specs</span>
            </button>
          </div>
        )}

        <div className="nypl-header-actions">
          {/* New Chat / Reset Button */}
          {activeView === 'canvas' && messageCount > 0 && (
            <button
              className="nypl-new-chat-btn"
              onClick={handleReset}
              title="Reset canvas and start fresh"
              aria-label="New Canvas"
            >
              <Plus size={14} className="text-nypl-red" />
              <span>New Canvas</span>
            </button>
          )}

          {/* Session / Lock Screen Button */}
          {isAuthenticated ? (
            <button
              className="nypl-auth-btn authenticated"
              onClick={onLogout}
              title="Click to Log Out and Lock Console"
              aria-label="Log Out"
            >
              <KeyRound size={13} />
              <span>Session Active</span>
            </button>
          ) : (
            onOpenKeyModal && (
              <button
                className="nypl-auth-btn"
                onClick={onOpenKeyModal}
                title="Unlock Research Console"
                aria-label="Unlock Console"
              >
                <Lock size={13} className="text-nypl-red" />
                <span>Unlock Console</span>
              </button>
            )
          )}

          {/* Live Status Badge */}
          <div className="nypl-status-badge" title="Multi-Agent Orchestrator Online">
            <div className="nypl-status-dot" />
            <span>Agent Online</span>
          </div>

          {/* Theme Toggle Button */}
          {onToggleTheme && (
            <button
              className="nypl-theme-btn"
              onClick={onToggleTheme}
              title={theme === 'light' ? 'Switch to Midnight Dark' : 'Switch to Reading Room Light'}
              aria-label="Toggle theme"
            >
              {theme === 'light' ? <Moon size={16} /> : <Sun size={16} />}
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
