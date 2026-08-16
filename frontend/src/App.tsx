import { useState, useMemo, useEffect, useCallback } from 'react';
import { Header } from './components/layout/Header';
import { TopCommandBar } from './components/canvas/TopCommandBar';
import { HorizontalPipelineTrace } from './components/canvas/HorizontalPipelineTrace';
import { CanvasGrid } from './components/canvas/CanvasGrid';
import { StarterCanvas } from './components/canvas/StarterCanvas';
import { ArchitectureExplainer } from './components/docs/ArchitectureExplainer';
import { AccessKeyModal } from './components/layout/AccessKeyModal';
import { useChatStream } from './hooks/useChatStream';
import { api } from './services/api';
import type { ChatMessage } from './types/a2ui';

export function App() {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    return (localStorage.getItem('nypl_theme') as 'light' | 'dark') || 'light';
  });

  const [activeView, setActiveView] = useState<'canvas' | 'explainer'>('canvas');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('nypl_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  const {
    messages,
    isLoading,
    activeCommand,
    setActiveCommand,
    sendMessage,
    clearChat,
  } = useChatStream();

  const [isKeyModalOpen, setIsKeyModalOpen] = useState(false);
  const [isAuthRequired, setIsAuthRequired] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check auth session status with backend on startup
  useEffect(() => {
    async function checkAuth() {
      const status = await api.verifyAuth();
      setIsAuthenticated(status.authenticated);
      setIsAuthRequired(status.requiresAuth);
      if (status.requiresAuth && !status.authenticated) {
        setIsKeyModalOpen(true);
      }
    }
    checkAuth();
  }, []);

  const handleLogin = useCallback(async (passcode: string): Promise<boolean> => {
    const success = await api.login(passcode);
    if (success) {
      setIsAuthenticated(true);
      setIsAuthRequired(false);
      return true;
    }
    return false;
  }, []);

  const handleLogout = useCallback(async () => {
    await api.logout();
    setIsAuthenticated(false);
    setIsAuthRequired(true);
    setIsKeyModalOpen(true);
    clearChat();
  }, [clearChat]);

  // Group messages into inquiry turns (User query + Model response)
  const inquiryTurns = useMemo(() => {
    const turns: { id: string; userMsg?: ChatMessage; botMsg: ChatMessage }[] = [];
    for (let i = 0; i < messages.length; i++) {
      const msg = messages[i];
      if (msg.role === 'user') {
        const nextMsg = messages[i + 1];
        if (nextMsg && nextMsg.role === 'model') {
          turns.push({ id: `turn-${msg.id}`, userMsg: msg, botMsg: nextMsg });
          i++; // skip next since it's paired
        } else {
          // Streaming placeholder before botMsg arrives
          turns.push({
            id: `turn-${msg.id}`,
            userMsg: msg,
            botMsg: {
              id: `placeholder-${Date.now()}`,
              role: 'model',
              content: '',
              isStreaming: true,
              timestamp: Date.now(),
            },
          });
        }
      } else if (msg.role === 'model') {
        turns.push({ id: `turn-${msg.id}`, botMsg: msg });
      }
    }
    return turns;
  }, [messages]);

  const [selectedInquiryIdx, setSelectedInquiryIdx] = useState<number | null>(null);

  // Default to the most recent inquiry turn if not explicitly selected
  const activeInquiryIndex = selectedInquiryIdx !== null && selectedInquiryIdx < inquiryTurns.length
    ? selectedInquiryIdx
    : Math.max(0, inquiryTurns.length - 1);

  const activeTurn = inquiryTurns[activeInquiryIndex];

  // Inquiries list for top tab bar
  const userInquiries = useMemo(() => {
    return inquiryTurns.map((t) => t.userMsg || t.botMsg);
  }, [inquiryTurns]);

  const handleSelectPrompt = (prompt: string, command: string) => {
    setActiveView('canvas');
    setActiveCommand(command);
    sendMessage(prompt, command);
    setSelectedInquiryIdx(null); // jump to latest
  };

  const handleActionClick = (promptText: string) => {
    setActiveView('canvas');
    sendMessage(promptText);
    setSelectedInquiryIdx(null); // jump to latest
  };

  const handleClearAll = () => {
    clearChat();
    setSelectedInquiryIdx(null);
  };

  return (
    <div className="nypl-app-shell">
      {/* Brand Header */}
      <Header
        theme={theme}
        onToggleTheme={toggleTheme}
        onResetChat={handleClearAll}
        messageCount={inquiryTurns.length}
        isAuthenticated={isAuthenticated}
        onOpenKeyModal={() => setIsKeyModalOpen(true)}
        onLogout={handleLogout}
        activeView={activeView}
        onSelectView={setActiveView}
      />

      {/* Main Content Area */}
      <main className="canvas-main-container">
        {activeView === 'explainer' ? (
          /* Hackathon Architecture & 30s Explainer View */
          <ArchitectureExplainer
            onSelectPrompt={handleSelectPrompt}
            onBackToCanvas={() => setActiveView('canvas')}
          />
        ) : (
          <>
            {/* Pinned Top Command Console */}
            <TopCommandBar
              isLoading={isLoading}
              activeCommand={activeCommand}
              onSelectCommand={setActiveCommand}
              onSubmitPrompt={(prompt) => {
                sendMessage(prompt);
                setSelectedInquiryIdx(null);
              }}
              inquiries={userInquiries}
              activeInquiryIndex={activeInquiryIndex}
              onSelectInquiry={(idx) => setSelectedInquiryIdx(idx)}
              onClearAll={handleClearAll}
            />

            {/* Dynamic Workspace */}
            {inquiryTurns.length === 0 ? (
              /* Empty / Initial Exploration State */
              <StarterCanvas onSelectPrompt={handleSelectPrompt} />
            ) : (
              /* Active Generative Canvas View */
              <div className="canvas-workspace animate-fade-in">
                {/* Horizontal Multi-Agent Reasoning Pipeline Stepper */}
                {activeTurn?.botMsg && (
                  <HorizontalPipelineTrace
                    traces={activeTurn.botMsg.traces}
                    isStreaming={activeTurn.botMsg.isStreaming}
                  />
                )}

                {/* Dynamic Adaptive Data Grid */}
                {activeTurn?.botMsg && (
                  <CanvasGrid
                    userQuery={activeTurn.userMsg?.content}
                    responseMessage={activeTurn.botMsg}
                    onActionClick={handleActionClick}
                  />
                )}
              </div>
            )}
          </>
        )}
      </main>

      {/* Access Passcode Gatekeeper Modal */}
      <AccessKeyModal
        isOpen={isKeyModalOpen}
        onClose={() => setIsKeyModalOpen(false)}
        onLogin={handleLogin}
        isDismissable={!isAuthRequired}
      />
    </div>
  );
}

export default App;
