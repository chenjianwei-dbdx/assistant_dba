import { useState, useRef, useEffect } from 'react'
import { Input, Button, Avatar } from 'antd'
import { SendOutlined } from '@ant-design/icons'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const eventSourceRef = useRef<EventSource | null>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    // 添加一条空的助手消息用于流式更新
    const assistantMessageId = (Date.now() + 1).toString()
    setMessages((prev) => [...prev, {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date()
    }])

    // 使用 EventSource 进行流式请求
    const encodedMessage = encodeURIComponent(input)
    const eventSource = new EventSource(`/api/chat/stream?message=${encodedMessage}`)
    eventSourceRef.current = eventSource

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'done') {
          eventSource.close()
          setLoading(false)
        } else if (data.type === 'content' && data.content) {
          setMessages((prev) => {
            const lastIndex = prev.length - 1
            const updated = [...prev]
            if (updated[lastIndex]?.role === 'assistant') {
              updated[lastIndex] = {
                ...updated[lastIndex],
                content: updated[lastIndex].content + data.content
              }
            }
            return updated
          })
        }
      } catch (e) {
        console.error('解析错误:', e)
      }
    }

    eventSource.onerror = () => {
      eventSource.close()
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-180px)]">
      <h1 className="text-2xl font-bold mb-4">AI 助手</h1>

      <div className="flex-1 overflow-y-auto space-y-4 mb-4 p-4 bg-gray-50 rounded-lg">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-20">
            <div className="text-4xl mb-2">🤖</div>
            <div className="text-lg">向我提问关于您的数据库的问题</div>
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex gap-3 max-w-[70%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <Avatar className={msg.role === 'user' ? 'bg-blue-500' : 'bg-gradient-to-br from-blue-500 to-purple-600'}>
                {msg.role === 'user' ? 'U' : 'AI'}
              </Avatar>
              <div className={`p-4 rounded-2xl ${msg.role === 'user'
                ? 'bg-blue-500 text-white rounded-tr-none'
                : 'bg-white border shadow-sm rounded-tl-none'
              }`}>
                <div className="whitespace-pre-wrap">{msg.content}</div>
                {msg.role === 'assistant' && msg.content === '' && loading && (
                  <span className="inline-block animate-pulse">思考中...</span>
                )}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="flex gap-3">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onPressEnter={handleSend}
          placeholder="输入您的问题..."
          disabled={loading}
          className="flex-1"
          size="large"
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={handleSend}
          loading={loading}
          size="large"
          className="bg-blue-500"
        >
          发送
        </Button>
      </div>
    </div>
  )
}
