import { useState, useEffect } from 'react'
import { Card, Row, Col, Table, Tag, Progress, Button, message } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import { ColumnsType } from 'antd/es/table'
import { useNavigate } from 'react-router-dom'

interface SlowQuery {
  key: string
  sql: string
  execution_time_ms: number
  timestamp: string
  suggestions: string[]
}

export default function Monitor() {
  const navigate = useNavigate()
  const [slowQueries, setSlowQueries] = useState<SlowQuery[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchSlowQueries()
  }, [])

  const fetchSlowQueries = async () => {
    setLoading(true)
    try {
      // 先获取连接列表
      const connRes = await fetch('/api/db/connections')
      const connData = await connRes.json()
      const connections = connData.connections || []

      if (connections.length === 0) {
        message.warning('请先添加数据库连接')
        setSlowQueries([])
        return
      }

      // 使用第一个连接查询慢查询
      const conn = connections[0]
      const res = await fetch('/api/db/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          connection_id: conn.id,
          sql: `SELECT query, calls, total_exec_time, mean_exec_time, max_exec_time
                FROM pg_stat_statements
                WHERE mean_exec_time > 100
                ORDER BY mean_exec_time DESC
                LIMIT 10`,
          limit: 10
        })
      })
      const data = await res.json()

      if (data.error) {
        // 如果 pg_stat_statements 不可用，返回空
        setSlowQueries([])
      } else {
        const queries = (data.rows || []).map((row: any, idx: number) => ({
          key: String(idx),
          sql: row.query || row.query_text || 'N/A',
          execution_time_ms: Math.round(row.mean_exec_time || row.total_exec_time || 0),
          timestamp: new Date().toISOString(),
          suggestions: ['建议添加索引', '考虑优化查询条件']
        }))
        setSlowQueries(queries)
      }
    } catch (e) {
      console.error('获取慢查询失败:', e)
      message.error('获取慢查询失败')
      setSlowQueries([])
    } finally {
      setLoading(false)
    }
  }

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
      title: '平均执行时间 (ms)',
      dataIndex: 'execution_time_ms',
      width: 120,
      render: (ms: number) => (
        <Tag color={ms > 3000 ? 'red' : ms > 1000 ? 'orange' : 'green'}>{ms}ms</Tag>
      )
    },
    { title: '时间戳', dataIndex: 'timestamp', width: 180 },
    {
      title: '优化建议',
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

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold m-0">性能监控</h1>
        <p className="text-gray-500 mt-1">实时性能监控</p>
      </div>

      <Row gutter={16} className="mb-6">
        <Col span={6}>
          <Card bordered className="shadow-sm">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">{slowQueries.length}</div>
              <div className="text-gray-500">慢查询数</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered className="shadow-sm">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">-</div>
              <div className="text-gray-500">每秒查询数 (QPS)</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered className="shadow-sm">
            <div className="text-center">
              <div className="text-3xl font-bold text-orange-600">-</div>
              <div className="text-gray-500">平均响应时间</div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered className="shadow-sm">
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">-</div>
              <div className="text-gray-500">运行时间</div>
            </div>
          </Card>
        </Col>
      </Row>

      <Card
        title="慢查询列表"
        bordered
        className="shadow-sm mb-6"
        extra={
          <Button icon={<ReloadOutlined />} onClick={fetchSlowQueries} loading={loading}>
            刷新
          </Button>
        }
      >
        {slowQueries.length === 0 && !loading ? (
          <div className="text-center py-8 text-gray-500">
            <p>暂无慢查询数据</p>
            <Button type="link" onClick={() => navigate('/connections')}>添加数据库连接</Button>
          </div>
        ) : (
          <Table
            columns={columns}
            dataSource={slowQueries}
            rowKey="key"
            pagination={false}
            loading={loading}
          />
        )}
      </Card>

      <Row gutter={16}>
        <Col span={12}>
          <Card title="查询性能" bordered className="shadow-sm">
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span>平均响应时间</span>
                  <span className="text-green-500">-</span>
                </div>
                <Progress percent={0} showInfo={false} strokeColor="#52c41a" />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span>P95 响应时间</span>
                  <span className="text-orange-500">-</span>
                </div>
                <Progress percent={0} showInfo={false} strokeColor="#faad14" />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span>P99 响应时间</span>
                  <span className="text-red-500">-</span>
                </div>
                <Progress percent={0} showInfo={false} strokeColor="#f5222d" />
              </div>
            </div>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="连接池状态" bordered className="shadow-sm">
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span>活跃连接</span>
                  <span>- / 100</span>
                </div>
                <Progress percent={0} showInfo={false} />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span>空闲连接</span>
                  <span>- / 100</span>
                </div>
                <Progress percent={0} showInfo={false} strokeColor="#1890ff" />
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
