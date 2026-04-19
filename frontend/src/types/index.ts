// 消息类型
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isStreaming?: boolean
}

// 会话类型
export interface Session {
  id: string
  title: string
  createdAt: Date
  messageCount: number
}

// 技能类型
export interface Skill {
  name: string
  version: string
  category: string
  description: string
  enabled: boolean
}

// WebSocket 消息格式
export interface WsSendMessage {
  message: string
  user_id: string
  session_id?: string
}

export interface WsChunkMessage {
  type: 'chunk'
  content: string
}

export interface WsCompleteMessage {
  type: 'complete'
  session_id: string
}

export type WsReceiveMessage = WsChunkMessage | WsCompleteMessage