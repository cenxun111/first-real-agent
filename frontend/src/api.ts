import type { ChatResponse } from './types';

const BASE_URL = 'http://localhost:8000';

export async function sendChat(sessionId: string, message: string): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!res.ok) throw new Error(`HTTP error ${res.status}`);
  return res.json();
}

export async function sendApproval(sessionId: string, action: 'approve' | 'reject'): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/api/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, action }),
  });
  if (!res.ok) throw new Error(`HTTP error ${res.status}`);
  return res.json();
}
