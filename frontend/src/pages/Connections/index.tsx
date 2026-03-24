import { Table, Button, Tag } from 'antd'

const columns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Host', dataIndex: 'host', key: 'host' },
  { title: 'Port', dataIndex: 'port', key: 'port' },
  { title: 'Database', dataIndex: 'database', key: 'database' },
  { title: 'Status', dataIndex: 'status', key: 'status', render: (status: string) => (
    <Tag color={status === 'connected' ? 'green' : 'red'}>{status}</Tag>
  )},
  { title: 'Actions', key: 'actions', render: () => (
    <Button size="small">Edit</Button>
  )},
]

const dataSource = [
  { key: '1', name: 'Production', host: '192.168.1.100', port: 3306, database: 'app_db', status: 'connected' },
  { key: '2', name: 'Staging', host: '192.168.1.101', port: 3306, database: 'app_staging', status: 'connected' },
]

export default function Connections() {
  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Database Connections</h1>
        <Button type="primary">Add Connection</Button>
      </div>
      <Table dataSource={dataSource} columns={columns} />
    </div>
  )
}
