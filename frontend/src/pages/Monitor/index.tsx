import { Card, Row, Col } from 'antd'

export default function Monitor() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Database Monitor</h1>
      <Row gutter={16}>
        <Col span={6}>
          <Card title="CPU Usage" bordered>
            <div className="text-3xl font-bold text-green-600">45%</div>
          </Card>
        </Col>
        <Col span={6}>
          <Card title="Memory" bordered>
            <div className="text-3xl font-bold text-blue-600">68%</div>
          </Card>
        </Col>
        <Col span={6}>
          <Card title="Connections" bordered>
            <div className="text-3xl font-bold text-purple-600">23/100</div>
          </Card>
        </Col>
        <Col span={6}>
          <Card title="QPS" bordered>
            <div className="text-3xl font-bold text-orange-600">1,234</div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}
