import { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Progress, Button } from 'antd'
import {
  DatabaseOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'

export default function Dashboard() {
  const navigate = useNavigate()
  const [connectionCount, setConnectionCount] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/db/connections')
      const data = await res.json()
      setConnectionCount(data.connections?.length || 0)
    } catch (e) {
      console.error('获取数据失败:', e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold m-0">控制台</h1>
        <p className="text-gray-500 mt-1">系统概览和快速访问</p>
      </div>

      <Row gutter={16} className="mb-6">
        <Col span={6}>
          <Card bordered hoverable className="shadow-sm">
            <Statistic
              title="活跃连接数"
              value={connectionCount}
              prefix={<DatabaseOutlined className="text-blue-500" />}
              valueStyle={{ color: '#1890ff' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered hoverable className="shadow-sm">
            <Statistic
              title="今日查询数"
              value={0}
              prefix={<ThunderboltOutlined className="text-green-500" />}
              valueStyle={{ color: '#52c41a' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered hoverable className="shadow-sm">
            <Statistic
              title="慢查询"
              value={0}
              prefix={<ClockCircleOutlined className="text-orange-500" />}
              valueStyle={{ color: '#faad14' }}
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered hoverable className="shadow-sm">
            <Statistic
              title="失败任务"
              value={0}
              prefix={<ExclamationCircleOutlined className="text-red-500" />}
              valueStyle={{ color: '#f5222d' }}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Card title="数据库健康状况" bordered className="shadow-sm">
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span>CPU 使用率</span>
                  <span className="text-gray-500">-</span>
                </div>
                <Progress percent={0} showInfo={false} strokeColor="#1890ff" />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span>内存使用率</span>
                  <span className="text-gray-500">-</span>
                </div>
                <Progress percent={0} showInfo={false} strokeColor="#52c41a" />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span>磁盘使用率</span>
                  <span className="text-gray-500">-</span>
                </div>
                <Progress percent={0} showInfo={false} strokeColor="#722ed1" />
              </div>
            </div>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="快捷操作" bordered className="shadow-sm">
            <div className="grid grid-cols-2 gap-3">
              <Button size="large" block onClick={() => navigate('/query')}>新建查询</Button>
              <Button size="large" block onClick={() => navigate('/monitor')}>查看慢查询</Button>
              <Button size="large" block onClick={() => navigate('/connections')}>检查索引</Button>
              <Button size="large" block onClick={() => navigate('/connections')}>立即备份</Button>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
