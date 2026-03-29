import { useState, useEffect } from 'react'
import { Card, Row, Col, Table, Tag, Button, Statistic, message, Modal, Tabs } from 'antd'
import { ReloadOutlined, PlayCircleOutlined } from '@ant-design/icons'
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

interface SlowQuery {
  key: string
  sql: string
  calls: number
  total_time_ms: number
  mean_time_ms: number
  max_time_ms: number
  min_time_ms: number
}

interface Suggestion {
  priority: string
  text: string
  sql?: string
}

export default function Monitor() {
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [overview, setOverview] = useState<any>(null)
  const [tableStats, setTableStats] = useState<TableStat[]>([])
  const [slowQueries, setSlowQueries] = useState<SlowQuery[]>([])
  const [errorMsg, setErrorMsg] = useState<string>('')
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [analysisText, setAnalysisText] = useState<string>('')
  const [executingSql, setExecutingSql] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    fetchAllData()
  }, [])

  const fetchAllData = async () => {
    setLoading(true)
    setErrorMsg('')
    try {
      const [overviewRes, tablesRes, slowQueriesRes] = await Promise.all([
        fetch('/api/monitor/overview'),
        fetch('/api/monitor/table-stats'),
        fetch('/api/monitor/slow-queries')
      ])

      const overviewData = await overviewRes.json()
      const tablesData = await tablesRes.json()
      const slowQueriesData = await slowQueriesRes.json()

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

      if (slowQueriesData.success && slowQueriesData.data?.queries) {
        const queries = slowQueriesData.data.queries.map((q: any, idx: number) => ({
          key: String(idx),
          sql: q.sql,
          calls: q.calls,
          total_time_ms: q.total_time_ms,
          mean_time_ms: q.mean_time_ms,
          max_time_ms: q.max_time_ms,
          min_time_ms: q.min_time_ms
        }))
        setSlowQueries(queries)
      } else if (slowQueriesData.error) {
        // pg_stat_statements 未启用时显示提示
        setSlowQueries([])
      }
    } catch (e) {
      setErrorMsg('获取监控数据失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchAnalysis = async () => {
    setAnalyzing(true)
    setSuggestions([])
    setAnalysisText('')
    try {
      const res = await fetch('/api/monitor/analyze')
      const data = await res.json()
      if (data.success) {
        setSuggestions(data.suggestions || [])
        setAnalysisText(data.analysis || '')
      } else {
        setSuggestions([{ priority: '错误', text: data.error || '分析失败' }])
      }
    } catch (e) {
      setSuggestions([{ priority: '错误', text: 'AI 分析请求失败' }])
    } finally {
      setAnalyzing(false)
    }
  }

  const executeSql = async (sql: string) => {
    Modal.confirm({
      title: '确认执行 SQL',
      content: (
        <div>
          <p className="mb-2">确定要执行以下 SQL 吗？</p>
          <pre className="bg-gray-100 p-2 rounded text-sm overflow-x-auto">{sql}</pre>
        </div>
      ),
      okText: '执行',
      cancelText: '取消',
      onOk: async () => {
        setExecutingSql(sql)
        try {
          const res = await fetch('/api/monitor/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sql })
          })
          const data = await res.json()
          if (data.success) {
            message.success(data.message || 'SQL 执行成功')
          } else {
            message.error(data.error || '执行失败')
          }
        } catch (e) {
          message.error('执行失败: 网络错误')
        } finally {
          setExecutingSql(null)
        }
      }
    })
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case '紧急': return 'red'
      case '严重': return 'red'
      case '警告': return 'orange'
      case '建议': return 'blue'
      case '错误': return 'red'
      default: return 'green'
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

  const slowQueryColumns: ColumnsType<SlowQuery> = [
    { title: 'SQL', dataIndex: 'sql', ellipsis: true, render: (t) => <code className="text-xs">{t}</code> },
    { title: '调用次数', dataIndex: 'calls', width: 100, align: 'right', render: (v) => v.toLocaleString() },
    { title: '总耗时(ms)', dataIndex: 'total_time_ms', width: 120, align: 'right', render: (v) => v.toLocaleString() },
    { title: '平均耗时(ms)', dataIndex: 'mean_time_ms', width: 120, align: 'right', render: (v) => <span style={{ color: v > 1000 ? '#f5222d' : v > 100 ? '#faad14' : '#52c41a' }}>{v.toLocaleString()}</span> },
    { title: '最大耗时(ms)', dataIndex: 'max_time_ms', width: 120, align: 'right', render: (v) => v.toLocaleString() },
    { title: '最小耗时(ms)', dataIndex: 'min_time_ms', width: 120, align: 'right' }
  ]

  const getHitRateColor = () => {
    if (!overview) return '#d9d9d9'
    return Number(overview.hit_rate) > 90 ? '#52c41a' : Number(overview.hit_rate) > 80 ? '#faad14' : '#f5222d'
  }

  const tabItems = [
    {
      key: 'overview',
      label: '性能概览',
      children: (
        <div>
          <Row gutter={16} className="mb-6">
            <Col span={6}>
              <Card variant="bordered">
                <Statistic title="当前连接数" value={overview?.connections || 0} />
              </Card>
            </Col>
            <Col span={6}>
              <Card variant="bordered">
                <Statistic title="活跃查询" value={overview?.active_queries || 0} />
              </Card>
            </Col>
            <Col span={6}>
              <Card variant="bordered">
                <Statistic
                  title="缓存命中率"
                  value={(overview?.hit_rate || '0') + '%'}
                  valueStyle={{ color: getHitRateColor() }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card variant="bordered">
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
        </div>
      )
    },
    {
      key: 'slow-queries',
      label: `慢查询分析${slowQueries.length > 0 ? ` (${slowQueries.length})` : ''}`,
      children: (
        <div>
          {slowQueries.length > 0 ? (
            <Card title="慢查询列表（基于 pg_stat_statements）" loading={loading}>
              <Table
                columns={slowQueryColumns}
                dataSource={slowQueries}
                pagination={{ pageSize: 10 }}
                size="small"
                scroll={{ x: 800 }}
              />
              <div className="mt-4 text-gray-500 text-sm">
                <p>注意：pg_stat_statements 需要扩展支持。如果列表为空，请联系 DBA 执行：</p>
                <code>CREATE EXTENSION pg_stat_statements;</code>
              </div>
            </Card>
          ) : (
            <Card title="慢查询分析" loading={loading}>
              <div className="text-center py-8 text-gray-500">
                <p>暂无慢查询数据</p>
                <p className="text-sm mt-2">可能原因：</p>
                <ul className="text-sm mt-2 list-disc list-inside">
                  <li>pg_stat_statements 扩展未启用</li>
                  <li>数据库中没有执行时间超过 100ms 的查询</li>
                </ul>
                <p className="text-sm mt-4">启用扩展命令：</p>
                <code className="text-xs bg-gray-100 p-2 rounded inline-block mt-2">
                  CREATE EXTENSION pg_stat_statements;
                </code>
              </div>
            </Card>
          )}
        </div>
      )
    },
    {
      key: 'ai-analysis',
      label: 'AI 优化建议',
      children: (
        <Card
          title="AI 性能分析"
          extra={
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchAnalysis}
              loading={analyzing}
              disabled={loading}
            >
              重新分析
            </Button>
          }
          loading={analyzing}
        >
          {analysisText ? (
            <div className="space-y-3">
              {suggestions.length > 0 ? (
                suggestions.map((s, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <Tag color={getPriorityColor(s.priority)} className="mt-1">
                      {s.priority}
                    </Tag>
                    <div className="flex-1">
                      <p className="m-0">{s.text}</p>
                      {s.sql && (
                        <Button
                          type="link"
                          size="small"
                          icon={<PlayCircleOutlined />}
                          loading={executingSql === s.sql}
                          onClick={() => s.sql && executeSql(s.sql)}
                          className="mt-1"
                        >
                          执行
                        </Button>
                      )}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-gray-600 whitespace-pre-wrap">{analysisText}</div>
              )}
            </div>
          ) : (
            <div className="text-center py-4 text-gray-400">
              <Button onClick={fetchAnalysis} loading={analyzing}>
                点击进行 AI 性能分析
              </Button>
            </div>
          )}
        </Card>
      )
    }
  ]

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

      <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
    </div>
  )
}
