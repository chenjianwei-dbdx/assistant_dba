import { useState, useEffect } from 'react'
import { Table, Button, Tag, Modal, Form, Input, Select, message, Space } from 'antd'
import { PlusOutlined, DeleteOutlined, DatabaseOutlined, LinkOutlined, DisconnectOutlined } from '@ant-design/icons'

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
      message.error('获取连接列表失败')
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
        message.success('连接创建成功')
        setModalVisible(false)
        form.resetFields()
        fetchConnections()
      }
    } catch (e) {
      message.error('创建连接失败')
    }
  }

  const handleDelete = async (id: string) => {
    try {
      const res = await fetch(`/api/db/connections/${id}`, { method: 'DELETE' })
      if (res.ok) {
        message.success('连接已删除')
        fetchConnections()
      }
    } catch (e) {
      message.error('删除连接失败')
    }
  }

  const handleConnect = async (conn: Connection) => {
    try {
      const res = await fetch('/api/db/connections/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          db_type: conn.db_type,
          host: conn.host,
          port: conn.port,
          database: conn.database,
          username: conn.username,
          password: ''
        })
      })
      const data = await res.json()
      if (data.success) {
        message.success(`已连接到 ${conn.name}`)
        fetchConnections()
      } else {
        message.error(`连接失败: ${data.error}`)
      }
    } catch (e) {
      message.error('连接失败')
    }
  }

  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <div className="flex items-center gap-2">
          <DatabaseOutlined className="text-blue-500" />
          <span className="font-medium">{name}</span>
        </div>
      )
    },
    { title: '类型', dataIndex: 'db_type', key: 'db_type', render: (type: string) => <Tag color="blue">{type.toUpperCase()}</Tag> },
    { title: '主机', dataIndex: 'host', key: 'host' },
    { title: '端口', dataIndex: 'port', key: 'port' },
    { title: '数据库', dataIndex: 'database', key: 'database' },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'status',
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>{active ? '活跃' : '未连接'}</Tag>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: Connection) => (
        <Space>
          <Button
            size="small"
            icon={record.is_active ? <DisconnectOutlined /> : <LinkOutlined />}
            onClick={() => handleConnect(record)}
            type={record.is_active ? 'default' : 'primary'}
            className={record.is_active ? '' : 'bg-blue-500'}
          >
            {record.is_active ? '断开' : '连接'}
          </Button>
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)} />
        </Space>
      )
    }
  ]

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold m-0">数据库连接</h1>
          <p className="text-gray-500 mt-1">管理您的数据库连接</p>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setModalVisible(true)}
          className="bg-blue-500"
        >
          添加连接
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
        title="添加数据库连接"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleAdd}>
          <Form.Item name="name" label="连接名称" rules={[{ required: true }]}>
            <Input placeholder="生产环境 MySQL" />
          </Form.Item>
          <Form.Item name="db_type" label="数据库类型" initialValue="postgresql">
            <Select onChange={(v) => {
              if (v === 'postgresql') form.setFieldValue('port', 5432)
              else if (v === 'mysql') form.setFieldValue('port', 3306)
            }}>
              {dbTypes.map((t) => (
                <Option key={t.value} value={t.value}>{t.label}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="host" label="主机地址" initialValue="127.0.0.1">
            <Input />
          </Form.Item>
          <Form.Item name="port" label="端口" initialValue={5432}>
            <Input type="number" />
          </Form.Item>
          <Form.Item name="database" label="数据库名" rules={[{ required: true }]}>
            <Input placeholder="app_db" />
          </Form.Item>
          <Form.Item name="username" label="用户名">
            <Input />
          </Form.Item>
          <Form.Item name="password" label="密码">
            <Input.Password />
          </Form.Item>
          <Form.Item className="mb-0">
            <div className="flex gap-2 justify-end">
              <Button onClick={() => setModalVisible(false)}>取消</Button>
              <Button type="primary" htmlType="submit" className="bg-blue-500">创建</Button>
            </div>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}
