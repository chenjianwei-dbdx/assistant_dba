import { useState } from 'react'
import { Button, Input, Table } from 'antd'

const { TextArea } = Input

export default function Query() {
  const [sql, setSql] = useState('')
  const [loading, setLoading] = useState(false)

  const handleExecute = async () => {
    setLoading(true)
    try {
      // TODO: 调用后端 API
      console.log('Executing SQL:', sql)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">SQL Query</h1>
      <TextArea
        rows={8}
        value={sql}
        onChange={(e) => setSql(e.target.value)}
        placeholder="Enter your SQL query..."
        className="mb-4 font-mono"
      />
      <div className="flex gap-2 mb-4">
        <Button type="primary" loading={loading} onClick={handleExecute}>
          Execute
        </Button>
        <Button>Format</Button>
        <Button>Explain</Button>
      </div>
      <Table
        dataSource={[]}
        columns={[]}
        pagination={{ pageSize: 10 }}
      />
    </div>
  )
}
