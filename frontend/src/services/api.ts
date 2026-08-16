/**
 * API Service Layer for NYC & NYPL AI Assistant Frontend.
 * Centralizes authentication, session management, and backend interactions.
 */

export interface AuthStatus {
  authenticated: boolean;
  requiresAuth: boolean;
}

export const api = {
  /**
   * Verifies the current session status using HttpOnly session cookies.
   */
  async verifyAuth(): Promise<AuthStatus> {
    try {
      const res = await fetch('/api/v1/auth/verify', {
        credentials: 'same-origin',
      });
      if (res.status === 401) {
        return { authenticated: false, requiresAuth: true };
      }
      if (res.ok) {
        return { authenticated: true, requiresAuth: false };
      }
      return { authenticated: false, requiresAuth: true };
    } catch {
      // Backend not reached (e.g. standalone frontend preview)
      return { authenticated: true, requiresAuth: false };
    }
  },

  /**
   * Logs in with a dashboard access passcode.
   */
  async login(passcode: string): Promise<boolean> {
    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ passcode }),
      });
      return res.ok;
    } catch {
      // Standalone mode fallback
      return true;
    }
  },

  /**
   * Clears the server-side session cookie on logout.
   */
  async logout(): Promise<void> {
    try {
      await fetch('/api/v1/auth/logout', {
        method: 'POST',
        credentials: 'same-origin',
      });
    } catch {
      // Ignore network errors during logout
    }
  },

  /**
   * Deletes an active multi-turn session from server memory.
   */
  async deleteSession(sessionId: string): Promise<void> {
    if (!sessionId) return;
    try {
      await fetch(`/api/v1/sessions/${encodeURIComponent(sessionId)}`, {
        method: 'DELETE',
        credentials: 'same-origin',
      });
    } catch {
      // Ignore cleanup network errors
    }
  },
};
