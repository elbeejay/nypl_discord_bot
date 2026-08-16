import { useState, useCallback, useEffect, useRef } from 'react';
import type { ChatMessage, A2UIPayload, AgentTraceStep } from '../types/a2ui';
import { api } from '../services/api';

const STORAGE_KEY = 'nypl_chat_session_v1';
const SESSION_ID_KEY = 'nypl_session_id';

export function useChatStream() {
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [sessionId, setSessionId] = useState<string | null>(() => {
    return localStorage.getItem(SESSION_ID_KEY) || null;
  });

  const sessionIdRef = useRef<string | null>(sessionId);
  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  const [isLoading, setIsLoading] = useState(false);
  const [activeCommand, setActiveCommand] = useState<string>('ask');

  // Persist messages
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    } catch (err) {
      console.warn('Failed to persist messages to localStorage', err);
    }
  }, [messages]);

  // Persist session ID
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem(SESSION_ID_KEY, sessionId);
    }
  }, [sessionId]);

  const clearChat = useCallback(() => {
    const currentId = sessionIdRef.current;
    if (currentId) {
      // Clean up server-side session
      api.deleteSession(currentId);
    }
    setMessages([]);
    setSessionId(null);
    sessionIdRef.current = null;
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(SESSION_ID_KEY);
  }, []);

  const sendMessage = useCallback(async (query: string, commandOverride?: string) => {
    if (!query.trim() || isLoading) return;

    const command = commandOverride || activeCommand;
    const userMsgId = `usr-${Date.now()}`;
    const botMsgId = `bot-${Date.now()}`;

    const userMessage: ChatMessage = {
      id: userMsgId,
      role: 'user',
      content: query.trim(),
      command,
      timestamp: Date.now(),
    };

    const initialBotMessage: ChatMessage = {
      id: botMsgId,
      role: 'model',
      content: '',
      command,
      isStreaming: true,
      traces: [],
      statusMessage: 'Routing to expert agent...',
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage, initialBotMessage]);
    setIsLoading(true);

    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      };

      const effectiveSessionId = sessionIdRef.current;
      const url = '/api/v1/chat/stream';

      const response = await fetch(url, {
        method: 'POST',
        headers,
        credentials: 'same-origin',
        body: JSON.stringify({
          query: query.trim(),
          command: command,
          session_id: effectiveSessionId,
          enable_a2ui: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let accumulatedText = '';
      let latestA2UI: A2UIPayload | null = null;
      let currentTraces: AgentTraceStep[] = [];
      let currentEvent = 'message';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) {
            currentEvent = 'message';
            continue;
          }

          if (trimmed.startsWith('event:')) {
            currentEvent = trimmed.replace('event:', '').trim();
          } else if (trimmed.startsWith('data:')) {
            const rawData = trimmed.replace('data:', '').trim();
            try {
              const parsed = JSON.parse(rawData);

              if (currentEvent === 'trace') {
                // Transition previous running steps to completed
                currentTraces = currentTraces.map((s) =>
                  s.status === 'running' ? { ...s, status: 'completed' as const } : s
                );

                const traceStep: AgentTraceStep = {
                  id: `trace-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
                  stage: parsed.stage || 'gateway',
                  title: parsed.title || 'Agent Step',
                  agent: parsed.agent,
                  tool: parsed.tool,
                  args: parsed.args,
                  detail: parsed.detail,
                  status: parsed.status || 'running',
                  timestamp: Date.now(),
                };
                currentTraces.push(traceStep);

                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === botMsgId
                      ? { ...msg, traces: [...currentTraces] }
                      : msg
                  )
                );
              } else if (currentEvent === 'status') {
                const statusMsg = parsed.message || 'Processing...';
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === botMsgId
                      ? { ...msg, statusMessage: statusMsg }
                      : msg
                  )
                );
              } else if (currentEvent === 'token') {
                const token = parsed.token || '';
                accumulatedText += token;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === botMsgId
                      ? { ...msg, content: accumulatedText, statusMessage: undefined }
                      : msg
                  )
                );
              } else if (currentEvent === 'a2ui') {
                latestA2UI = parsed as A2UIPayload;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === botMsgId
                      ? { ...msg, a2ui: latestA2UI }
                      : msg
                  )
                );
              } else if (currentEvent === 'done') {
                if (parsed.session_id) {
                  sessionIdRef.current = parsed.session_id;
                  setSessionId(parsed.session_id);
                  localStorage.setItem(SESSION_ID_KEY, parsed.session_id);
                }
                // Mark all traces as completed on done
                currentTraces = currentTraces.map((s) =>
                  s.status === 'running' ? { ...s, status: 'completed' as const } : s
                );
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === botMsgId
                      ? { ...msg, traces: [...currentTraces] }
                      : msg
                  )
                );
              } else if (currentEvent === 'error') {
                accumulatedText += `\n\n⚠️ Error: ${parsed.error || 'Unknown error'}`;
                currentTraces = currentTraces.map((s) =>
                  s.status === 'running' ? { ...s, status: 'error' as const } : s
                );
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === botMsgId
                      ? { ...msg, content: accumulatedText, traces: [...currentTraces], statusMessage: undefined }
                      : msg
                  )
                );
              }
            } catch (err) {
              console.error('Error parsing SSE data chunk', err, rawData);
            }
          }
        }
      }

      // Mark streaming done and finalize terminal status on all traces
      currentTraces = currentTraces.map((s) =>
        s.status === 'running' ? { ...s, status: 'completed' as const } : s
      );

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === botMsgId
            ? {
                ...msg,
                isStreaming: false,
                statusMessage: undefined,
                traces: [...currentTraces],
              }
            : msg
        )
      );
    } catch (err: any) {
      console.error('Chat stream error', err);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === botMsgId
            ? {
                ...msg,
                content: msg.content || `⚠️ Network or agent error: ${err.message || 'Failed to connect to agent backend.'}`,
                isStreaming: false,
                statusMessage: undefined,
                traces: (msg.traces || []).map((s) =>
                  s.status === 'running' ? { ...s, status: 'error' as const } : s
                ),
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, activeCommand]);

  return {
    messages,
    isLoading,
    activeCommand,
    setActiveCommand,
    sendMessage,
    clearChat,
  };
}
