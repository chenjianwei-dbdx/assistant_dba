import { useState, useEffect } from 'react'
import { Card, Row, Col, Table, Tag, Button, Statistic } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'

interface TableStat {
  key: string
  schema: string
  table: string
  seq_scans: number
  index_scans: number
  index_scans_ratio: string
  inserts: number
  updates: number
  deletes: number
  live_rows: number
  dead_rows: number
}

export default function Monitor() {
  const [loading, setLoading] = useState(false)
  const [overview, setOverview] = useState<any>(null)
  const [tableStats, setTableStats] = useState<TableStat[]>([])
  const [errorMsg, setErrorMsg] = useState<string>('')

  useEffect(() => {
    fetchAllData()
  }, [])

  const fetchAllData = async () => {
    setLoading(true)
    setErrorMsg('')
    try {
      const [overviewRes, tablesRes] = await Promise.all([
        fetch('/api/monitor/overview'),
        fetch('/api/monitor/table-stats')
      ])

      const overviewData = await overviewRes.json()
      const tablesData = await tablesRes.json()

      if (overviewData.success && overviewData.data) {
        const d = overviewData.data
        let hitRate = '100'
        if (d.block_reads > 0) {
          hitRate = ((d.block_hits / (d.block_hits + d.block_reads) * 100).toFixed(1))
        }
        setOverview({
          connections: d.connections,
          active_queries: d.active_queries,
          hit_rate: hitRate,
          commit: d.transactions_commit,
          rollback: d.transactions_rollback
        })
      }

      if (tablesData.success && tablesData.data?.tables) {
        const tables = tablesData.data.tables.map((t: any, idx: number) => {
          const idxRatio = t.index_scans > 0 && t.seq_scans > 0
            ? (t.index_scans / (t.seq_scans + t.index_scans) * 100).toFixed(1)
            : '0'
          return {
            key: String(idx),
            schema: t.schema,
            table: t.table,
            seq_scans: t.seq_scans,
            index_scans: t.index_scans,
            index_scans_ratio: idxRatio,
            inserts: t.inserts,
            updates: t.updates,
            deletes: t.deletes,
            live_rows: t.live_rows,
            dead_rows: t.dead_rows
          }
        })
        setTableStats(tables)
      }
    } catch (e) {
      setErrorMsg('获取监控数据失败')
    } finally {
      setLoading(false)
    }
  }

  const tableColumns: ColumnsType<TableStat> = [
    { title: '表名', dataIndex: 'table', width: 150, render: (t) => <code className="text-sm">{t}</code> },
    { title: 'Seq Scan', dataIndex: 'seq_scans', width: 100, align: 'right', render: (v) => <span style={{ color: v > 10000 ? '#faad14' : undefined }}>{v.toLocaleString()}</span> },
    { title: 'Index Scan', dataIndex: 'index_scans', width: 100, align: 'right', render: (v) => <span style={{ color: '#52c41a' }}>{v.toLocaleString()}</span> },
    { title: '索引率%', dataIndex: 'index_scans_ratio', width: 80, align: 'right' },
    { title: '插入', dataIndex: 'inserts', width: 80, align: 'right' },
    { title: '更新', dataIndex: 'updates', width: 80, align: 'right' },
    { title: '删除', dataIndex: 'deletes', width: 80, align: 'right' },
    { title: '存活行', dataIndex: 'live_rows', width: 100, align: 'right' },
    { title: '死亡行', dataIndex: 'dead_rows', width: 100, align: 'right', render: (v) => <Tag color={v > 100 ? 'red' : v > 0 ? 'orange' : 'green'}>{v.toLocaleString()}</Tag> }
  ]

  const getHitRateColor = () => {
    if (!overview) return '#d9d9d9'
    return Number(overview.hit_rate) > 90 ? '#52c41a' : Number(overview.hit_rate) > 80 ? '#faad14' : '#f5222d'
  }

  return (
    <div className="p-6">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold m-0">性能监控</h1>
          <p className="text-gray-500 mt-1">PostgreSQL 数据库实时性能指标</p>
        </div>
        <Button icon={<ReloadOutlined />} onClick={fetchAllData} loading={loading}>
          刷新
        </Button>
      </div>

      {errorMsg && <Tag color="red">{errorMsg}</Tag>}

      <Row gutter={16} className="mb-6">
        <Col span={6}>
          <Card bordered>
            <Statistic title="当前连接数" value={overview?.connections || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered>
            <Statistic title="活跃查询" value={overview?.active_queries || 0} />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered>
            <Statistic
              title="缓存命中率"
              value={(overview?.hit_rate || '0') + '%'}
              valueStyle={{ color: getHitRateColor() }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered>
            <Statistic
              title="事务提交/回滚"
              value={`${(overview?.commit || 0).toLocaleString()} / ${overview?.rollback || 0}`}
            />
          </Card>
        </Col>
      </Row>

      <Card title="表扫描统计" className="mb-6" loading={loading}>
        <Table
          columns={tableColumns}
          dataSource={tableStats}
          pagination={{ pageSize: 10 }}
          size="small"
        />
      </Card>

      <Card title="优化建议" bordered>
        <div className="space-y-2">
          {overview && Number(overview.hit_rate) < 90 && (
            <Tag color="red">警告: 缓存命中率低于 90%，建议增加 shared_buffers</Tag>
          )}
          {tableStats.filter(t => t.dead_rows > 100).length > 0 && (
            <Tag color="orange">有些表死元组较多，建议执行 VACUUM</Tag>
          )}
          {tableStats.filter(t => Number(t.index_scans_ratio) < 50).length > 0 && (
            <Tag color="orange">部分表索引扫描率偏低，考虑添加索引</Tag>
          )}
          {!errorMsg && tableStats.length === 0 && (
            <Tag>暂无明显性能问题</Tag>
          )}
        </div>
      </Card>
    </div>
  )
}
