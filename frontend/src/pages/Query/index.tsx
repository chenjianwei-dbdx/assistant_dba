import { useState, useEffect } from 'react'
import { Button, Select, Table, Tabs, Space, message } from 'antd'
import {
  PlayCircleOutlined,
  FormatPainterOutlined,
  ThunderboltOutlined,
  ExportOutlined
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

const { Option } = Select

interface QueryResult {
  key: string
  [key: string]: any
}

export default function Query() {
  const [sql, setSql] = useState('SELECT * FROM db_connections LIMIT 10;')
  const [loading, setLoading] = useState(false)
  const [connectionId, setConnectionId] = useState<string>('')
  const [connections, setConnections] = useState<any[]>([])
  const [queryResult, setQueryResult] = useState<{ columns: string[]; rows: any[] } | null>(null)
  const [executionTime, setExecutionTime] = useState<number>(0)

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
          <Table
            columns={columns}
            dataSource={queryResult.rows.map((row, index) => ({ ...row, key: String(index) }))}
            rowKey="key"
            pagination={{ pageSize: 10, showSizeChanger: true }}
            size="small"
            scroll={{ x: 800 }}
          />
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
        <div className="bg-gray-800 rounded-lg p-4 text-white font-mono text-sm">
          <textarea
            className="w-full bg-transparent text-white font-mono text-sm outline-none resize-none"
            rows={4}
            value={sql}
            onChange={(e) => setSql(e.target.value)}
            placeholder="输入 SQL 语句..."
          />
        </div>
      </div>

      <div className="flex gap-2 mb-4">
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          onClick={handleExecute}
          loading={loading}
          className="bg-blue-500"
        >
          执行
        </Button>
        <Button icon={<FormatPainterOutlined />}>格式化</Button>
        <Button icon={<ThunderboltOutlined />}>执行计划</Button>
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
