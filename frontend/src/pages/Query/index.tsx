import { useState } from 'react'
import { Button, Select, Table, Tabs, Space, Tag, message } from 'antd'
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
  id: number
  name: string
  email: string
  status: string
  created_at: string
}

const mockColumns: ColumnsType<QueryResult> = [
  { title: 'ID', dataIndex: 'id', width: 80 },
  { title: 'Name', dataIndex: 'name', width: 150 },
  { title: 'Email', dataIndex: 'email' },
  { title: 'Status', dataIndex: 'status', width: 100, render: (s: string) => <Tag color={s === 'active' ? 'green' : 'default'}>{s}</Tag> },
  { title: 'Created At', dataIndex: 'created_at', width: 180 },
]

const mockData: QueryResult[] = [
  { key: '1', id: 1, name: 'John Doe', email: 'john@example.com', status: 'active', created_at: '2024-01-15 10:30:00' },
  { key: '2', id: 2, name: 'Jane Smith', email: 'jane@example.com', status: 'active', created_at: '2024-01-14 09:15:00' },
]

export default function Query() {
  const [sql] = useState('SELECT * FROM users LIMIT 10;')
  const [loading, setLoading] = useState(false)
  const [connectionId, setConnectionId] = useState<string>('')

  const handleExecute = async () => {
    if (!connectionId) {
      message.warning('Please select a connection first')
      return
    }
    setLoading(true)
    try {
      const res = await fetch('/api/db/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ connection_id: connectionId, sql })
      })
      const data = await res.json()
      console.log('Query result:', data)
      message.success('Query executed')
    } catch (e) {
      message.error('Query failed')
    } finally {
      setLoading(false)
    }
  }

  const tabItems = [
    {
      key: 'results',
      label: 'Results',
      children: (
        <Table
          columns={mockColumns}
          dataSource={mockData}
          rowKey="key"
          pagination={{ pageSize: 10, showSizeChanger: true }}
          size="small"
          scroll={{ x: 800 }}
        />
      )
    },
    {
      key: 'explain',
      label: 'Explain',
      children: (
        <pre className="bg-gray-100 p-4 rounded text-xs overflow-auto">
          {`{
  "id": 1,
  "select_type": "SIMPLE",
  "table": "users",
  "type": "ALL",
  "possible_keys": null,
  "key": null,
  "rows": 1000
}`}
        </pre>
      )
    },
    {
      key: 'history',
      label: 'History',
      children: <div className="p-4 text-gray-500">Query history will appear here</div>
    }
  ]

  return (
    <div className="h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold m-0">SQL Query</h1>
        <Space>
          <Select
            placeholder="Select connection"
            value={connectionId || undefined}
            onChange={setConnectionId}
            style={{ width: 200 }}
            showSearch
            filterOption={(input, option) =>
              (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
            }
          >
            <Option value="conn1">Production MySQL</Option>
            <Option value="conn2">Staging PostgreSQL</Option>
          </Select>
        </Space>
      </div>

      <div className="mb-4">
        <div className="bg-gray-800 rounded-lg p-4 text-white font-mono text-sm">
          <pre className="whitespace-pre-wrap mb-0">{sql}</pre>
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
          Execute
        </Button>
        <Button icon={<FormatPainterOutlined />}>Format</Button>
        <Button icon={<ThunderboltOutlined />}>Explain</Button>
        <Button icon={<ExportOutlined />}>Export</Button>
      </div>

      <div className="flex-1 bg-white border rounded-lg overflow-hidden">
        <Tabs items={tabItems} className="p-4" />
      </div>
    </div>
  )
}
