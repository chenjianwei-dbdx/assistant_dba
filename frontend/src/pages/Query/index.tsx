import { useState, useEffect } from 'react'
import { Button, Select, Table, Tabs, Space, message, Switch, Input, Spin, Alert } from 'antd'
import {
  PlayCircleOutlined,
  FormatPainterOutlined,
  ThunderboltOutlined,
  ExportOutlined,
  RobotOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

const { Option } = Select
const { TextArea } = Input

interface QueryResult {
  key: string
  [key: string]: any
}

type AiStatus = 'idle' | 'generating' | 'generated' | 'executing' | 'completed' | 'error'

export default function Query() {
  const [sql, setSql] = useState('SELECT * FROM db_connections LIMIT 10;')
  const [loading, setLoading] = useState(false)
  const [connectionId, setConnectionId] = useState<string>('')
  const [connections, setConnections] = useState<any[]>([])
  const [queryResult, setQueryResult] = useState<{ columns: string[]; rows: any[] } | null>(null)
  const [executionTime, setExecutionTime] = useState<number>(0)

  // AI 辅助相关状态
  const [aiMode, setAiMode] = useState(false)
  const [userQuery, setUserQuery] = useState('')
  const [aiStatus, setAiStatus] = useState<AiStatus>('idle' as AiStatus)
  const [generatedSql, setGeneratedSql] = useState('')
  const [aiExplanation, setAiExplanation] = useState('')
  const [aiSummary, setAiSummary] = useState('')
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    fetchConnections()
  }, [])

  const fetchConnections = async () => {
    try {
      const res = await fetch('/api/db/connections')
      const data = await res.json()
      setConnections(data.connections || [])
    } catch (e) {
      message.error('获取连接列表失败')
    }
  }

  const handleExecute = async () => {
    if (!connectionId) {
      message.warning('请先选择数据库连接')
      return
    }
    if (!sql.trim()) {
      message.warning('请输入 SQL 语句')
      return
    }
    setLoading(true)
    setQueryResult(null)
    try {
      const startTime = Date.now()
      const res = await fetch('/api/db/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ connection_id: connectionId, sql, limit: 1000 })
      })
      const data = await res.json()
      const elapsed = Date.now() - startTime
      setExecutionTime(data.execution_time_ms || elapsed)

      if (data.error) {
        message.error('查询失败: ' + data.error)
      } else {
        setQueryResult({
          columns: data.columns || [],
          rows: data.rows || []
        })
        message.success(`查询成功，返回 ${data.row_count || 0} 行`)
      }
    } catch (e) {
      message.error('查询执行失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAiGenerate = async () => {
    if (!connectionId) {
      message.warning('请先选择数据库连接')
      return
    }
    if (!userQuery.trim()) {
      message.warning('请输入自然语言查询需求')
      return
    }
    setAiStatus('generating')
    setErrorMessage('')
    setGeneratedSql('')
    setAiExplanation('')
    setAiSummary('')
    try {
      const res = await fetch('/api/db/text2sql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ connection_id: connectionId, query: userQuery })
      })
      const data = await res.json()
      if (data.success && data.data) {
        // 处理元查询（查询表列表等）
        if (data.data.is_meta_query && data.data.tables) {
          setAiExplanation(data.data.explanation || '')
          setAiStatus('completed')
          // 直接显示表列表
          setQueryResult({
            columns: ['表名', '模块', '描述'],
            rows: data.data.tables.map((t: any, i: number) => ({
              key: String(i),
              '表名': t.name,
              '模块': t.module,
              '描述': t.description
            }))
          })
          return
        }
        setGeneratedSql(data.data.sql)
        setAiExplanation(data.data.explanation || '')
        setAiStatus('generated')
        setSql(data.data.sql)
      } else {
        setErrorMessage(data.error || 'SQL 生成失败')
        setAiStatus('error')
      }
    } catch (e) {
      setErrorMessage('调用 AI 服务失败')
      setAiStatus('error')
    }
  }

  const handleAiExecute = async () => {
    if (!generatedSql.trim()) {
      message.warning('没有可执行的 SQL')
      return
    }
    setAiStatus('executing')
    setLoading(true)
    setErrorMessage('')
    try {
      const res = await fetch('/api/db/text2sql/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ connection_id: connectionId, sql: generatedSql })
      })
      const data = await res.json()
      if (data.success && data.data) {
        setQueryResult({
          columns: data.data.columns || [],
          rows: data.data.rows || []
        })
        setExecutionTime(data.data.execution_time_ms || 0)
        setAiSummary(data.data.summary || '')
        setAiStatus('completed')
        message.success(`查询成功，返回 ${data.data.row_count || 0} 行`)
      } else {
        setErrorMessage(data.error || '执行失败')
        setAiStatus('error')
      }
    } catch (e) {
      setErrorMessage('执行失败')
      setAiStatus('error')
    } finally {
      setLoading(false)
    }
  }

  const handleAiRetry = () => {
    setAiStatus('idle')
    setUserQuery('')
    setGeneratedSql('')
    setAiExplanation('')
    setAiSummary('')
    setErrorMessage('')
  }

  // Helper to check if AI is generating
  const isAiGenerating = (): boolean => aiStatus === 'generating'

  const columns: ColumnsType<QueryResult> = queryResult
    ? queryResult.columns.map((col) => ({
        title: col,
        dataIndex: col,
        key: col,
        ellipsis: true,
        width: 150
      }))
    : []

  const tabItems = [
    {
      key: 'results',
      label: '结果',
      children: (
        queryResult && queryResult.rows.length > 0 ? (
          <div className="space-y-4">
            {aiMode && aiStatus === 'completed' && aiSummary && (
              <Alert
                message="数据摘要"
                description={aiSummary}
                type="success"
                showIcon
              />
            )}
            <Table
              columns={columns}
              dataSource={queryResult.rows.map((row, index) => ({ ...row, key: String(index) }))}
              rowKey="key"
              pagination={{ pageSize: 10, showSizeChanger: true }}
              size="small"
              scroll={{ x: 800 }}
            />
          </div>
        ) : (
          <div className="p-8 text-center text-gray-500">
            {sql.trim() ? '点击"执行"按钮运行查询' : '请输入 SQL 语句'}
          </div>
        )
      )
    },
    {
      key: 'explain',
      label: '执行计划',
      children: (
        <div className="p-4 text-gray-500">
          点击"执行计划"按钮查看查询执行计划
        </div>
      )
    },
    {
      key: 'history',
      label: '历史记录',
      children: <div className="p-4 text-gray-500">查询历史将显示在这里</div>
    }
  ]

  return (
    <div className="h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold m-0">SQL 查询</h1>
        <Space>
          <span className="text-gray-500 flex items-center gap-2">
            <RobotOutlined />
            <span>AI 辅助</span>
            <Switch checked={aiMode} onChange={setAiMode} size="small" />
          </span>
          <Select
            placeholder="选择连接"
            value={connectionId || undefined}
            onChange={setConnectionId}
            style={{ width: 200 }}
            showSearch
            filterOption={(input, option) =>
              (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
            }
          >
            {connections.map((conn) => (
              <Option key={conn.id} value={conn.id}>{conn.name}</Option>
            ))}
          </Select>
        </Space>
      </div>

      <div className="mb-4">
        {aiMode ? (
          <div className="space-y-4">
            {aiStatus === 'idle' && (
              <div>
                <TextArea
                  className="mb-2"
                  rows={3}
                  value={userQuery}
                  onChange={(e) => setUserQuery(e.target.value)}
                  placeholder="用自然语言描述你的查询需求，例如：查询所有订单数量大于10的用户"
                />
                <Button
                  type="primary"
                  icon={<RobotOutlined />}
                  onClick={handleAiGenerate}
                  loading={isAiGenerating()}
                  className="bg-blue-500"
                >
                  生成 SQL
                </Button>
              </div>
            )}

            {aiStatus === 'generating' && (
              <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg">
                <Spin />
                <span>正在分析需求...</span>
              </div>
            )}

            {(aiStatus === 'generated' || aiStatus === 'executing' || aiStatus === 'completed') && (
              <div className="space-y-4">
                <Alert
                  message="AI 已生成 SQL"
                  description={aiExplanation}
                  type="info"
                  showIcon
                />
                <div className="bg-gray-800 rounded-lg p-4 text-white font-mono text-sm">
                  <pre className="whitespace-pre-wrap">{generatedSql}</pre>
                </div>
                {aiStatus === 'generated' && (
                  <Button
                    type="primary"
                    icon={<PlayCircleOutlined />}
                    onClick={handleAiExecute}
                    loading={loading}
                    className="bg-green-500"
                  >
                    执行此 SQL
                  </Button>
                )}
                {aiStatus === 'executing' && (
                  <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg">
                    <Spin />
                    <span>正在执行...</span>
                  </div>
                )}
              </div>
            )}

            {aiStatus === 'error' && (
              <Alert
                message="出错了"
                description={errorMessage}
                type="error"
                showIcon
                action={
                  <Button size="small" onClick={handleAiRetry}>
                    重试
                  </Button>
                }
              />
            )}
          </div>
        ) : (
          <div className="bg-gray-800 rounded-lg p-4 text-white font-mono text-sm">
            <textarea
              className="w-full bg-transparent text-white font-mono text-sm outline-none resize-none"
              rows={4}
              value={sql}
              onChange={(e) => setSql(e.target.value)}
              placeholder="输入 SQL 语句..."
            />
          </div>
        )}
      </div>

      <div className="flex gap-2 mb-4">
        {!aiMode && (
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={handleExecute}
            loading={loading}
            className="bg-blue-500"
          >
            执行
          </Button>
        )}
        {!aiMode && <Button icon={<FormatPainterOutlined />}>格式化</Button>}
        {!aiMode && <Button icon={<ThunderboltOutlined />}>执行计划</Button>}
        <Button icon={<ExportOutlined />}>导出</Button>
        {executionTime > 0 && (
          <span className="ml-4 text-gray-500 self-center">
            执行时间: {executionTime}ms
          </span>
        )}
      </div>

      <div className="flex-1 bg-white border rounded-lg overflow-hidden">
        <Tabs items={tabItems} className="p-4" />
      </div>
    </div>
  )
}
