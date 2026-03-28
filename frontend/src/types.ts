export type MessageRole = 'user' | 'agent' | 'system';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
}

export interface PendingTool {
  name: string;
  args: Record<string, unknown>;
  tool_call_id: string;
}

export interface ChatResponse {
  status: 'success' | 'PAUSED_FOR_APPROVAL';
  response?: string;
  pending_tool?: PendingTool;
}
