import { Card, Row, Col, Table, Tag, Progress } from 'antd'
import { ColumnsType } from 'antd/es/table'

interface SlowQuery {
  key: string
  sql: string
  execution_time_ms: number
  timestamp: string
  suggestions: string[]
}

const slowQueriesData: SlowQuery[] = [
  {
    key: '1',
    sql: 'SELECT * FROM orders WHERE date > "2024-01-01"',
    execution_time_ms: 5420,
    timestamp: '2024-01-15 10:30:00',
    suggestions: ['Add index on date column', 'Avoid SELECT *']
  },
  {
    key: '2',
    sql: 'SELECT u.*, o.* FROM users u LEFT JOIN orders o ON u.id = o.user_id',
    execution_time_ms: 3200,
    timestamp: '2024-01-15 09:15:00',
    suggestions: ['Use covering index']
  },
]

const columns: ColumnsType<SlowQuery> = [
  {
    title: 'SQL',
    dataIndex: 'sql',
    ellipsis: true,
    width: 300,
    render: (sql: string) => (
      <code className="text-xs bg-gray-100 px-2 py-1 rounded">{sql.slice(0, 50)}...</code>
    )
  },
  {
    title: 'Time (ms)',
    dataIndex: 'execution_time_ms',
    width: 120,
    render: (ms: number) => (
      <Tag color={ms > 3000 ? 'red' : ms > 1000 ? 'orange' : 'green'}>{ms}ms</Tag>
    )
  },
  { title: 'Timestamp', dataIndex: 'timestamp', width: 180 },
  {
    title: 'Suggestions',
    dataIndex: 'suggestions',
    render: (suggestions: string[]) => (
      <div className="flex flex-wrap gap-1">
        {suggestions.map((s, i) => (
          <Tag key={i} color="blue">{s}</Tag>
        ))}
      </div>
    )
  }
]

export default function Monitor() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold m-0">Database Monitor</h1>
        <p className="text-gray-500 mt-1">Real-time performance monitoring</p>
      </div>

      <Row gutter={16} className="mb-6">
        <Col span={6}>
          <Card bordered className="shadow-sm">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">23</div>
              <div className="text-gray-500">Active Connections</div>
              <Progress percent={23} showInfo={false} className="mt-2" />
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered className="shadow-sm">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">1,234</div>
              <div className="text-gray-500">QPS</div>
              <Progress percent={60} showInfo={false} className="mt-2" />
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered className="shadow-sm">
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-600">12</div>
              <div className="text-gray-500">Slow Queries</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered className="shadow-sm">
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">99.9%</div>
              <div className="text-gray-500">Uptime</div>
            </div>
          </Card>
        </Col>
      </Row>

      <Card title="Slow Queries" bordered className="shadow-sm mb-6">
        <Table
          columns={columns}
          dataSource={slowQueriesData}
          rowKey="key"
          pagination={false}
        />
      </Card>

      <Row gutter={16}>
        <Col span={12}>
          <Card title="Query Performance" bordered className="shadow-sm">
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span>Avg Response Time</span>
                  <span className="text-green-500">45ms</span>
                </div>
                <Progress percent={30} showInfo={false} strokeColor="#52c41a" />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span>P95 Response Time</span>
                  <span className="text-orange-500">120ms</span>
                </div>
                <Progress percent={50} showInfo={false} strokeColor="#faad14" />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span>P99 Response Time</span>
                  <span className="text-red-500">350ms</span>
                </div>
                <Progress percent={70} showInfo={false} strokeColor="#f5222d" />
              </div>
            </div>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Connection Pool" bordered className="shadow-sm">
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span>Active</span>
                  <span>23 / 100</span>
                </div>
                <Progress percent={23} showInfo={false} />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span>Idle</span>
                  <span>77 / 100</span>
                </div>
                <Progress percent={77} showInfo={false} strokeColor="#1890ff" />
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
