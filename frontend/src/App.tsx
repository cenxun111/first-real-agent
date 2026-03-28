import { useState, useRef, useEffect, useCallback } from 'react';
import { ChatMessage } from './components/ChatMessage';
import { TypingIndicator } from './components/TypingIndicator';
import { ChatInput } from './components/ChatInput';
import { ApprovalModal } from './components/ApprovalModal';
import { sendChat, sendApproval } from './api';
import type { Message, PendingTool } from './types';
import styles from './App.module.css';

function getSessionId(): string {
  let id = localStorage.getItem('agentSessionId');
  if (!id) {
    id = 'session_' + Math.random().toString(36).slice(2, 11);
    localStorage.setItem('agentSessionId', id);
  }
  return id;
}

const SESSION_ID = getSessionId();

export default function App() {
  const [messages, setMessages] = useState<Message[]>([
    { id: 'init', role: 'agent', content: "Welcome! I'm your AI Agent. What can I help you with today? 🚀" }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [pendingTool, setPendingTool] = useState<PendingTool | null>(null);
  const feedRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight, behavior: 'smooth' });
    }, 50);
  }, []);

  useEffect(() => { scrollToBottom(); }, [messages, isLoading, scrollToBottom]);

  const handleApiResponse = useCallback((data: Awaited<ReturnType<typeof sendChat>>) => {
    if (data.status === 'PAUSED_FOR_APPROVAL' && data.pending_tool) {
      setPendingTool(data.pending_tool);
    } else if (data.status === 'success' && data.response) {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'agent',
        content: data.response!,
      }]);
    }
  }, []);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    setInput('');
    setMessages(prev => [...prev, { id: Date.now().toString(), role: 'user', content: text }]);
    setIsLoading(true);

    try {
      const data = await sendChat(SESSION_ID, text);
      handleApiResponse(data);
    } catch {
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'system', content: '⚠️ Network error. Could not reach the server.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApproval = async (action: 'approve' | 'reject') => {
    setPendingTool(null);
    setIsLoading(true);
    try {
      const data = await sendApproval(SESSION_ID, action);
      handleApiResponse(data);
    } catch {
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'system', content: '⚠️ Failed to process approval.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.root}>
      {/* Animated background blobs */}
      <div className={styles.bg}>
        <div className={`${styles.blob} ${styles.blob1}`} />
        <div className={`${styles.blob} ${styles.blob2}`} />
        <div className={`${styles.blob} ${styles.blob3}`} />
      </div>

      <main className={styles.chat}>
        {/* Header */}
        <header className={styles.header}>
          <div>
            <h1 className={styles.headerTitle}>First Real Agent</h1>
            <p className={styles.headerSub}>Powered by FastAPI · LiteLLM · React</p>
          </div>
          <div className={styles.statusBadge}>
            <span className={styles.dot} />
            Online
          </div>
        </header>

        {/* Feed */}
        <div className={styles.feed} ref={feedRef}>
          {messages.map(msg => (
            <ChatMessage key={msg.id} message={msg} />
          ))}
          {isLoading && <TypingIndicator />}
        </div>

        {/* Input */}
        <ChatInput
          value={input}
          onChange={setInput}
          onSend={handleSend}
          disabled={isLoading}
        />
      </main>

      {/* Approval Modal */}
      {pendingTool && (
        <ApprovalModal
          tool={pendingTool}
          onApprove={() => handleApproval('approve')}
          onReject={() => handleApproval('reject')}
        />
      )}
    </div>
  );
}
