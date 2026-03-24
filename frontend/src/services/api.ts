/**
 * API Service
 * 前端 API 调用层
 */

const API_BASE = '/api'

interface ApiResponse<T> {
  data?: T
  error?: string
}

async function request<T>(
  endpoint: string,
  options?: RequestInit
): Promise<ApiResponse<T>> {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    })

    const data = await res.json()

    if (!res.ok) {
      return { error: data.detail || 'Request failed' }
    }

    return { data }
  } catch (e) {
    return { error: e instanceof Error ? e.message : 'Network error' }
  }
}

// Chat API
export const chatApi = {
  send: (message: string, sessionId?: string) =>
    request<{ message: string; session_id: string; tool_used?: string }>('/chat/', {
      method: 'POST',
      body: JSON.stringify({ message, session_id: sessionId }),
    }),

  stream: (message: string, sessionId?: string) =>
    new EventSource(`${API_BASE}/chat/stream?message=${encodeURIComponent(message)}${sessionId ? `&session_id=${sessionId}` : ''}`),
}

// DB Connections API
export const dbApi = {
  list: () =>
    request<{ connections: any[] }>('/db/connections'),

  create: (conn: any) =>
    request<any>('/db/connections', {
      method: 'POST',
      body: JSON.stringify(conn),
    }),

  delete: (id: string) =>
    request<void>(`/db/connections/${id}`, { method: 'DELETE' }),

  test: (conn: any) =>
    request<any>('/db/connections/test', {
      method: 'POST',
      body: JSON.stringify(conn),
    }),

  query: (connectionId: string, sql: string, limit = 1000) =>
    request<any>('/db/query', {
      method: 'POST',
      body: JSON.stringify({ connection_id: connectionId, sql, limit }),
    }),
}

// Admin API
export const adminApi = {
  tools: () => request<{ tools: any[] }>('/admin/tools'),
  health: () => request<any>('/admin/health'),
}
