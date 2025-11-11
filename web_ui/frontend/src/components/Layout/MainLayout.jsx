import React, { useState } from 'react'
import { Layout, Menu, theme } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  DatabaseOutlined,
  ShareAltOutlined,
  CheckCircleOutlined,
  SearchOutlined,
  BarChartOutlined
} from '@ant-design/icons'

const { Header, Sider, Content } = Layout

const menuItems = [
  {
    key: '/',
    icon: <DashboardOutlined />,
    label: '首页概览'
  },
  {
    key: '/catalog',
    icon: <DatabaseOutlined />,
    label: '数据资产目录'
  },
  {
    key: '/lineage',
    icon: <ShareAltOutlined />,
    label: '数据溯源'
  },
  {
    key: '/quality',
    icon: <CheckCircleOutlined />,
    label: '数据质量'
  },
  {
    key: '/explorer',
    icon: <SearchOutlined />,
    label: '数据浏览'
  },
  {
    key: '/reports',
    icon: <BarChartOutlined />,
    label: '业务报表'
  }
]

export default function MainLayout({ children }) {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const {
    token: { colorBgContainer }
  } = theme.useToken()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider 
        collapsible 
        collapsed={collapsed} 
        onCollapse={setCollapsed}
        theme="dark"
      >
        <div style={{ 
          height: 32, 
          margin: 16, 
          background: 'rgba(255, 255, 255, 0.3)',
          borderRadius: 4,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontWeight: 'bold'
        }}>
          {collapsed ? 'DC' : '数据中台'}
        </div>
        <Menu
          theme="dark"
          selectedKeys={[location.pathname]}
          mode="inline"
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ 
          padding: '0 24px', 
          background: colorBgContainer,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <h2 style={{ margin: 0 }}>高速公路省级收费中心数据中台</h2>
        </Header>
        <Content style={{ 
          margin: '24px 16px', 
          padding: 24, 
          minHeight: 280,
          background: colorBgContainer,
          borderRadius: 8
        }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  )
}

