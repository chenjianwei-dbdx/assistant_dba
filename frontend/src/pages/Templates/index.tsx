import { useState, useEffect } from 'react'
import { Table, Button, Tag, Modal, Form, Input, Select, Space, message, Popconfirm, InputNumber } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, PlayCircleOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

const { Option } = Select

interface Template {
  id: number
  name: string
  category: string
  description: string
  sql_pattern: string
  parameters: { name: string; type: string; default: any; description: string }[]
  examples: string
  use_count: number
  is_favorite: boolean
}

const CATEGORIES = [
  { value: 'performance', label: '性能分析' },
  { value: 'slow_query', label: '慢查询' },
  { value: 'table_stats', label: '表统计' },
  { value: 'index_stats', label: '索引统计' },
  { value: 'vacuum', label: 'Vacuum' },
  { value: 'connection', label: '连接管理' },
  { value: 'database', label: '数据库' },
  { value: 'custom', label: '自定义' }
]

export default function Templates() {
  const [templates, setTemplates] = useState<Template[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null)
  const [form] = Form.useForm()
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

  // 执行模板相关状态
  const [executeModalVisible, setExecuteModalVisible] = useState(false)
  const [executingTemplate, setExecutingTemplate] = useState<Template | null>(null)
  const [executeParams, setExecuteParams] = useState<Record<string, any>>({})
  const [executeLoading, setExecuteLoading] = useState(false)
  const [resultModalVisible, setResultModalVisible] = useState(false)
  const [queryResult, setQueryResult] = useState<{ columns: string[]; rows: any[] } | null>(null)

  useEffect(() => {
    fetchTemplates()
  }, [selectedCategory])

  const fetchTemplates = async () => {
    setLoading(true)
    try {
      const url = selectedCategory
        ? `/api/templates?category=${selectedCategory}`
        : '/api/templates'
      const res = await fetch(url)
      const data = await res.json()
      setTemplates(data.templates || [])
    } catch (e) {
      message.error('获取模板失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingTemplate(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (template: Template) => {
    setEditingTemplate(template)
    form.setFieldsValue(template)
    setModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      const res = await fetch(`/api/templates/${id}`, { method: 'DELETE' })
      if (res.ok) {
        message.success('删除成功')
        fetchTemplates()
      }
    } catch (e) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      const url = editingTemplate
        ? `/api/templates/${editingTemplate.id}`
        : '/api/templates'
      const method = editingTemplate ? 'PUT' : 'POST'

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values)
      })

      if (res.ok) {
        message.success(editingTemplate ? '更新成功' : '创建成功')
        setModalVisible(false)
        fetchTemplates()
      }
    } catch (e) {
      message.error('保存失败')
    }
  }

  const handleExecute = (template: Template) => {
    // 初始化参数（使用默认值）
    const defaultParams: Record<string, any> = {}
    template.parameters.forEach(p => {
      defaultParams[p.name] = p.default
    })
    setExecutingTemplate(template)
    setExecuteParams(defaultParams)
    setExecuteModalVisible(true)
  }

  const handleExecuteWithParams = async () => {
    if (!executingTemplate) return
    setExecuteLoading(true)
    try {
      const res = await fetch('/api/templates/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_id: executingTemplate.id,
          params: executeParams
        })
      })
      const data = await res.json()
      if (data.success) {
        setQueryResult({
          columns: data.columns || [],
          rows: data.rows || []
        })
        setResultModalVisible(true)
        setExecuteModalVisible(false)
      } else {
        message.error(data.error || '执行失败')
      }
    } catch (e) {
      message.error('执行失败')
    } finally {
      setExecuteLoading(false)
    }
  }

  const handleParamChange = (name: string, value: any) => {
    setExecuteParams(prev => ({ ...prev, [name]: value }))
  }

  const columns: ColumnsType<Template> = [
    { title: '名称', dataIndex: 'name', key: 'name', width: 200 },
    {
      title: '分类',
      dataIndex: 'category',
      key: 'category',
      width: 100,
      render: (cat: string) => {
        const c = CATEGORIES.find(c => c.value === cat)
        return <Tag color="blue">{c?.label || cat}</Tag>
      }
    },
    { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
    {
      title: '使用次数',
      dataIndex: 'use_count',
      key: 'use_count',
      width: 80,
      align: 'right'
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
      render: (_: any, record: Template) => (
        <Space>
          <Button
            size="small"
            icon={<PlayCircleOutlined />}
            onClick={() => handleExecute(record)}
          >
            执行
          </Button>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="确定删除?"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold m-0">SQL 模板库</h1>
          <p className="text-gray-500 mt-1">DBA 常用查询模板，高效执行</p>
        </div>
        <Space>
          <Select
            placeholder="选择分类"
            allowClear
            value={selectedCategory}
            style={{ width: 150 }}
            onChange={(v) => setSelectedCategory(v || null)}
          >
            {CATEGORIES.map(c => (
              <Option key={c.value} value={c.value}>{c.label}</Option>
            ))}
          </Select>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd} className="bg-blue-500">
            添加模板
          </Button>
        </Space>
      </div>

      <Table
        dataSource={templates}
        columns={columns}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
        expandable={{
          expandedRowRender: (record) => (
            <div>
              <p className="mb-2"><strong>SQL:</strong></p>
              <pre className="bg-gray-100 p-3 rounded text-sm overflow-x-auto">
                {record.sql_pattern}
              </pre>
              {record.examples && (
                <>
                  <p className="mb-2 mt-4"><strong>示例:</strong> {record.examples}</p>
                </>
              )}
              {record.parameters && record.parameters.length > 0 && (
                <p className="mt-2 text-gray-500 text-sm">
                  <strong>参数:</strong> {record.parameters.map(p => `${p.name}(${p.default})`).join(', ')}
                </p>
              )}
            </div>
          )
        }}
      />

      <Modal
        title={editingTemplate ? '编辑模板' : '添加模板'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={700}
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="name" label="模板名称" rules={[{ required: true }]}>
            <Input placeholder="例如: AWR-TopSQL(耗时)" />
          </Form.Item>

          <Form.Item name="category" label="分类" rules={[{ required: true }]}>
            <Select>
              {CATEGORIES.map(c => (
                <Option key={c.value} value={c.value}>{c.label}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="模板功能描述" />
          </Form.Item>

          <Form.Item name="sql_pattern" label="SQL 模板" rules={[{ required: true }]}>
            <Input.TextArea
              rows={8}
              placeholder="SQL 模板，使用 {param} 作为参数占位符"
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>

          <Form.Item name="examples" label="使用示例">
            <Input.TextArea rows={2} placeholder="例如: 查看耗时最长的 20 条 SQL" />
          </Form.Item>

          <Form.Item className="mb-0">
            <div className="flex justify-end gap-2">
              <Button onClick={() => setModalVisible(false)}>取消</Button>
              <Button type="primary" htmlType="submit" className="bg-blue-500">
                保存
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Modal>

      {/* 执行模板参数输入弹窗 */}
      <Modal
        title={`执行模板: ${executingTemplate?.name || ''}`}
        open={executeModalVisible}
        onCancel={() => setExecuteModalVisible(false)}
        footer={null}
        width={600}
      >
        {executingTemplate && (
          <div className="space-y-4">
            {executingTemplate.description && (
              <div className="text-gray-600">{executingTemplate.description}</div>
            )}
            <div className="bg-gray-100 rounded p-3 text-sm">
              <div className="font-mono whitespace-pre-wrap">{executingTemplate.sql_pattern}</div>
            </div>
            {executingTemplate.parameters && executingTemplate.parameters.length > 0 ? (
              <div className="space-y-3">
                <div className="font-medium">参数设置:</div>
                <div className="grid grid-cols-2 gap-4">
                  {executingTemplate.parameters.map(p => (
                    <div key={p.name} className="flex flex-col">
                      <label className="text-sm text-gray-600 mb-1">
                        {p.name} {p.description && `- ${p.description}`}
                      </label>
                      {p.type === 'integer' ? (
                        <InputNumber
                          value={executeParams[p.name]}
                          onChange={(v) => handleParamChange(p.name, v)}
                          min={0}
                          style={{ width: '100%' }}
                        />
                      ) : (
                        <Input
                          value={executeParams[p.name]}
                          onChange={(e) => handleParamChange(p.name, e.target.value)}
                        />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-gray-500">此模板不需要参数</div>
            )}
            <div className="flex justify-end gap-2 pt-4 border-t">
              <Button onClick={() => setExecuteModalVisible(false)}>取消</Button>
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={handleExecuteWithParams}
                loading={executeLoading}
                className="bg-green-500"
              >
                执行
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* 执行结果展示弹窗 */}
      <Modal
        title="执行结果"
        open={resultModalVisible}
        onCancel={() => setResultModalVisible(false)}
        footer={null}
        width={800}
      >
        {queryResult && (
          <Table
            dataSource={queryResult.rows.map((row, index) => ({ ...row, key: index }))}
            columns={queryResult.columns.map(col => ({
              title: col,
              dataIndex: col,
              key: col,
              ellipsis: true
            }))}
            rowKey="key"
            pagination={{ pageSize: 10, showSizeChanger: true }}
            size="small"
            scroll={{ x: 600 }}
          />
        )}
      </Modal>
    </div>
  )
}
