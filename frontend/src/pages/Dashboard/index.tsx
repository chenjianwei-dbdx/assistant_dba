import { Card, Row, Col, Statistic, Progress, Button } from 'antd'
import {
  DatabaseOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons'

export default function Dashboard() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold m-0">Dashboard</h1>
        <p className="text-gray-500 mt-1">System overview and quick access</p>
      </div>

      <Row gutter={16} className="mb-6">
        <Col span={6}>
          <Card bordered hoverable className="shadow-sm">
            <Statistic
              title="Active Connections"
              value={12}
              prefix={<DatabaseOutlined className="text-blue-500" />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered hoverable className="shadow-sm">
            <Statistic
              title="Queries Today"
              value={156}
              prefix={<ThunderboltOutlined className="text-green-500" />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered hoverable className="shadow-sm">
            <Statistic
              title="Slow Queries"
              value={3}
              prefix={<ClockCircleOutlined className="text-orange-500" />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered hoverable className="shadow-sm">
            <Statistic
              title="Failed Jobs"
              value={0}
              prefix={<ExclamationCircleOutlined className="text-red-500" />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Card title="Database Health" bordered className="shadow-sm">
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span>CPU Usage</span>
                  <span className="text-gray-500">45%</span>
                </div>
                <Progress percent={45} showInfo={false} strokeColor="#1890ff" />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span>Memory</span>
                  <span className="text-gray-500">68%</span>
                </div>
                <Progress percent={68} showInfo={false} strokeColor="#52c41a" />
              </div>
              <div>
                <div className="flex justify-between mb-1">
                  <span>Disk</span>
                  <span className="text-gray-500">32%</span>
                </div>
                <Progress percent={32} showInfo={false} strokeColor="#722ed1" />
              </div>
            </div>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Quick Actions" bordered className="shadow-sm">
            <div className="grid grid-cols-2 gap-3">
              <Button size="large" block>New Query</Button>
              <Button size="large" block>View Slow Queries</Button>
              <Button size="large" block>Check Indexes</Button>
              <Button size="large" block>Backup Now</Button>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
