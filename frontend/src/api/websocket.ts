import type { WsSendMessage, WsReceiveMessage } from '../types'

export type MessageHandler = (data: WsReceiveMessage) => void
export type ErrorHandler = (error: Event) => void
export type OpenHandler = () => void
export type CloseHandler = () => void

export class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private messageHandler: MessageHandler | null = null
  private errorHandler: ErrorHandler | null = null
  private openHandler: OpenHandler | null = null
  private closeHandler: CloseHandler | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5

  constructor(url: string = '/ws/chat') {
    // 开发环境使用代理，生产环境使用相对路径
    if (import.meta.env.DEV) {
      this.url = `ws://localhost:8080${url}`
    } else {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      this.url = `${protocol}//${window.location.host}${url}`
    }
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        this.reconnectAttempts = 0
        this.openHandler?.()
        resolve()
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WsReceiveMessage
          this.messageHandler?.(data)
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }

      this.ws.onerror = (error) => {
        this.errorHandler?.(error)
        reject(error)
      }

      this.ws.onclose = () => {
        this.closeHandler?.()
        this.tryReconnect()
      }
    })
  }

  private tryReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`)
      setTimeout(() => {
        this.connect().catch(console.error)
      }, 1000 * this.reconnectAttempts)
    }
  }

  send(data: WsSendMessage): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.error('WebSocket is not connected')
    }
  }

  onMessage(handler: MessageHandler): void {
    this.messageHandler = handler
  }

  onError(handler: ErrorHandler): void {
    this.errorHandler = handler
  }

  onOpen(handler: OpenHandler): void {
    this.openHandler = handler
  }

  onClose(handler: CloseHandler): void {
    this.closeHandler = handler
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }
}

// 全局 WebSocket 客户端实例
export const wsClient = new WebSocketClient()