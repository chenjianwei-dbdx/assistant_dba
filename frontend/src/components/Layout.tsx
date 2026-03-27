import { Outlet, Link, useLocation } from 'react-router-dom'
import { Layout as AntLayout, Menu } from 'antd'

const { Header, Sider, Content } = AntLayout

const menuItems = [
  { key: '/dashboard', label: <Link to="/dashboard">控制台</Link> },
  { key: '/query', label: <Link to="/query">SQL 查询</Link> },
  { key: '/monitor', label: <Link to="/monitor">性能监控</Link> },
  { key: '/connections', label: <Link to="/connections">数据库连接</Link> },
  { key: '/chat', label: <Link to="/chat">AI 助手</Link> },
]

export function Layout() {
  const location = useLocation()

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header className="bg-gray-900 text-white flex items-center">
        <div className="text-xl font-bold">DBA 智能助手</div>
      </Header>
      <AntLayout>
        <Sider width={200} className="bg-gray-100">
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            style={{ height: '100%', borderRight: 0 }}
          />
        </Sider>
        <Content className="p-6 bg-gray-50">
          <div className="bg-white p-6 rounded-lg shadow-sm min-h-[calc(100vh-64px)]">
            <Outlet />
          </div>
        </Content>
      </AntLayout>
    </AntLayout>
  )
}
