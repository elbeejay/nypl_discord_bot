import React, { useState } from 'react';
import { KeyRound, Eye, EyeOff, ShieldCheck, AlertCircle, Loader2, X } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose?: () => void;
  onLogin: (passcode: string) => Promise<boolean>;
  isDismissable?: boolean;
}

export const AccessKeyModal: React.FC<Props> = ({
  isOpen,
  onClose,
  onLogin,
  isDismissable = false,
}) => {
  const [inputKey, setInputKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputKey.trim()) {
      setErrorMessage('Please enter the Access Passcode.');
      return;
    }

    setIsVerifying(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const isValid = await onLogin(inputKey.trim());
      if (isValid) {
        setSuccessMessage('Passcode verified. Secure session active.');
        setInputKey('');
        setTimeout(() => {
          if (onClose) onClose();
        }, 500);
      } else {
        setErrorMessage('Invalid Passcode. Please check and try again.');
      }
    } catch {
      setErrorMessage('Unable to reach server. Please check network connection.');
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="a2ui-modal-backdrop animate-fade-in" style={{ zIndex: 1000 }}>
      <div
        className="a2ui-modal-content access-key-card animate-fade-in"
        style={{ maxWidth: '440px', width: '92%', padding: '0', overflow: 'hidden' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header Ribbon */}
        <div className="access-key-header">
          <div className="access-key-lion-badge">🦁</div>
          <div>
            <h3 className="serif-heading access-key-title">NYPL Research Console</h3>
            <p className="access-key-subtitle">Protected Access & AI Orchestration Gateway</p>
          </div>
          {isDismissable && onClose && (
            <button
              className="a2ui-modal-close"
              onClick={onClose}
              aria-label="Close modal"
              style={{ top: '14px', right: '14px' }}
            >
              <X size={18} />
            </button>
          )}
        </div>

        <form onSubmit={handleSubmit} className="access-key-body">
          <p className="access-key-instruction">
            Enter the authorized Access Passcode to unlock the research console and execute multi-agent Gemini queries.
          </p>

          <div className="access-key-input-wrapper">
            <KeyRound size={16} className="access-key-icon text-nypl-red" />
            <input
              type={showKey ? 'text' : 'password'}
              placeholder="Enter Access Passcode..."
              value={inputKey}
              onChange={(e) => {
                setInputKey(e.target.value);
                setErrorMessage(null);
              }}
              className="access-key-input"
              autoFocus
            />
            <button
              type="button"
              className="access-key-visibility-toggle"
              onClick={() => setShowKey(!showKey)}
              title={showKey ? 'Hide key' : 'Show key'}
              tabIndex={-1}
            >
              {showKey ? <EyeOff size={15} /> : <Eye size={15} />}
            </button>
          </div>

          {errorMessage && (
            <div className="access-key-alert error animate-fade-in">
              <AlertCircle size={14} />
              <span>{errorMessage}</span>
            </div>
          )}

          {successMessage && (
            <div className="access-key-alert success animate-fade-in">
              <ShieldCheck size={14} />
              <span>{successMessage}</span>
            </div>
          )}

          <div className="access-key-footer">
            <div className="access-key-rate-info">
              <ShieldCheck size={12} className="text-nypl-red" />
              <span>Gated with IP Sliding-Window Rate Limiting (15 req/min)</span>
            </div>

            <button
              type="submit"
              disabled={isVerifying}
              className="access-key-submit-btn"
            >
              {isVerifying ? (
                <>
                  <Loader2 size={14} className="animate-spin" />
                  <span>Verifying...</span>
                </>
              ) : (
                <span>Unlock Console</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
