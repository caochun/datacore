import React, { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Table, Tag, Spin } from 'antd'
import {
  DatabaseOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined
} from '@ant-design/icons'
import api from '../utils/api'
import ReactECharts from 'echarts-for-react'

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({})
  const [recentTables, setRecentTables] = useState([])
  const [qualityTrend, setQualityTrend] = useState([])

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [statsData, tablesData, qualityData] = await Promise.all([
        api.get('/stats/overview'),
        api.get('/tables?limit=10'),
        api.get('/quality/metrics?days=7')
      ])

      console.log('Dashboard data loaded:', { statsData, tablesData: tablesData?.length, qualityData: qualityData?.length })
      setStats(statsData || {})
      setRecentTables(tablesData && tablesData.length > 0 ? tablesData.slice(0, 5) : [])
      setQualityTrend(qualityData || [])
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      setStats({})
      setRecentTables([])
      setQualityTrend([])
    } finally {
      setLoading(false)
    }
  }

  const qualityChartOption = {
    title: {
      text: '数据质量趋势（最近7天）',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: qualityTrend && qualityTrend.length > 0 ? qualityTrend.map(item => item.metric_date).reverse() : []
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: '综合质量得分',
        type: 'line',
        data: qualityTrend && qualityTrend.length > 0 ? qualityTrend.map(item => item.overall_quality_score).reverse() : [],
        smooth: true,
        itemStyle: { color: '#1890ff' }
      }
    ]
  }

  const tableColumns = [
    {
      title: '表名',
      dataIndex: 'table_name_cn',
      key: 'table_name_cn',
      render: (text, record) => text || record.table_name
    },
    {
      title: '数据分层',
      dataIndex: 'data_layer',
      key: 'data_layer',
      render: (layer) => {
        const colors = {
          staging: 'blue',
          ods: 'green',
          dwd: 'orange',
          dws: 'purple',
          ads: 'red',
          metadata: 'default'
        }
        return <Tag color={colors[layer] || 'default'}>{layer}</Tag>
      }
    },
    {
      title: '业务域',
      dataIndex: 'business_domain',
      key: 'business_domain'
    }
  ]

  if (loading) {
    return <Spin size="large" style={{ display: 'block', textAlign: 'center', marginTop: 100 }} />
  }

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="数据表总数"
              value={Object.values(stats.tables_by_layer || {}).reduce((a, b) => a + b, 0)}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平均质量得分"
              value={stats.quality?.avg_score || 0}
              precision={2}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: stats.quality?.avg_score >= 95 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="质量告警数"
              value={stats.quality?.alert_count || 0}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="数据分层分布"
              value={Object.keys(stats.tables_by_layer || {}).length}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={16}>
          <Card title="数据质量趋势">
            <ReactECharts option={qualityChartOption} style={{ height: 300 }} />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="数据分层统计">
            {Object.entries(stats.tables_by_layer || {}).map(([layer, count]) => (
              <div key={layer} style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span>{layer.toUpperCase()}</span>
                  <span style={{ fontWeight: 'bold' }}>{count}</span>
                </div>
                <div style={{ 
                  height: 8, 
                  background: '#f0f0f0', 
                  borderRadius: 4,
                  overflow: 'hidden'
                }}>
                  <div style={{
                    height: '100%',
                    width: `${(count / Object.values(stats.tables_by_layer || {}).reduce((a, b) => a + b, 0)) * 100}%`,
                    background: '#1890ff'
                  }} />
                </div>
              </div>
            ))}
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24}>
          <Card title="最近更新的数据表">
            <Table
              columns={tableColumns}
              dataSource={recentTables}
              rowKey="table_name"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

