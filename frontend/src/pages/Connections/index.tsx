import { useState, useEffect } from 'react'
import { Table, Button, Tag, Modal, Form, Input, Select, message } from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined, DatabaseOutlined } from '@ant-design/icons'

const { Option } = Select

interface Connection {
  id: string
  name: string
  db_type: string
  host: string
  port: number
  database: string
  username: string
  is_active: boolean
}

const dbTypes = [
  { value: 'mysql', label: 'MySQL' },
  { value: 'postgresql', label: 'PostgreSQL' },
  { value: 'sqlite', label: 'SQLite' },
]

export default function Connections() {
  const [connections, setConnections] = useState<Connection[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchConnections()
  }, [])

  const fetchConnections = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/db/connections')
      const data = await res.json()
      setConnections(data.connections || [])
    } catch (e) {
      message.error('Failed to fetch connections')
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = async (values: any) => {
    try {
      const res = await fetch('/api/db/connections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values)
      })
      if (res.ok) {
        message.success('Connection created')
        setModalVisible(false)
        form.resetFields()
        fetchConnections()
      }
    } catch (e) {
      message.error('Failed to create connection')
    }
  }

  const handleDelete = async (id: string) => {
    try {
      const res = await fetch(`/api/db/connections/${id}`, { method: 'DELETE' })
      if (res.ok) {
        message.success('Connection deleted')
        fetchConnections()
      }
    } catch (e) {
      message.error('Failed to delete connection')
    }
  }

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <div className="flex items-center gap-2">
          <DatabaseOutlined className="text-blue-500" />
          <span className="font-medium">{name}</span>
        </div>
      )
    },
    { title: 'Type', dataIndex: 'db_type', key: 'db_type', render: (type: string) => <Tag color="blue">{type.toUpperCase()}</Tag> },
    { title: 'Host', dataIndex: 'host', key: 'host' },
    { title: 'Port', dataIndex: 'port', key: 'port' },
    { title: 'Database', dataIndex: 'database', key: 'database' },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'status',
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>{active ? 'Active' : 'Inactive'}</Tag>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Connection) => (
        <div className="flex gap-2">
          <Button size="small" icon={<EditOutlined />} />
          <Button
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          />
        </div>
      )
    }
  ]

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold m-0">Database Connections</h1>
          <p className="text-gray-500 mt-1">Manage your database connections</p>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setModalVisible(true)}
          className="bg-blue-500"
        >
          Add Connection
        </Button>
      </div>

      <Table
        dataSource={connections}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={false}
        className="shadow-sm"
      />

      <Modal
        title="Add Database Connection"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleAdd}>
          <Form.Item name="name" label="Connection Name" rules={[{ required: true }]}>
            <Input placeholder="MySQL Production" />
          </Form.Item>
          <Form.Item name="db_type" label="Database Type" initialValue="mysql">
            <Select>
              {dbTypes.map((t) => (
                <Option key={t.value} value={t.value}>{t.label}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="host" label="Host" initialValue="localhost">
            <Input />
          </Form.Item>
          <Form.Item name="port" label="Port" initialValue={3306}>
            <Input type="number" />
          </Form.Item>
          <Form.Item name="database" label="Database" rules={[{ required: true }]}>
            <Input placeholder="app_db" />
          </Form.Item>
          <Form.Item name="username" label="Username">
            <Input />
          </Form.Item>
          <Form.Item name="password" label="Password">
            <Input.Password />
          </Form.Item>
          <Form.Item className="mb-0">
            <div className="flex gap-2 justify-end">
              <Button onClick={() => setModalVisible(false)}>Cancel</Button>
              <Button type="primary" htmlType="submit" className="bg-blue-500">Create</Button>
            </div>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
