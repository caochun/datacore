import React, { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Table, Tag, Spin, Select } from 'antd'
import { CheckCircleOutlined, WarningOutlined, CloseCircleOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import api from '../utils/api'

const { Option } = Select

export default function DataQuality() {
  const [loading, setLoading] = useState(false)
  const [dashboardData, setDashboardData] = useState({})
  const [qualityMetrics, setQualityMetrics] = useState([])
  const [days, setDays] = useState(30)

  useEffect(() => {
    loadData()
  }, [days])

  const loadData = async () => {
    try {
      setLoading(true)
      const [dashboard, metrics] = await Promise.all([
        api.get('/quality/dashboard'),
        api.get(`/quality/metrics?days=${days}`)
      ])
      console.log('Quality data loaded:', { dashboard, metrics: metrics?.length })
      setDashboardData(dashboard || { summary: {}, trend: [] })
      setQualityMetrics(metrics || [])
    } catch (error) {
      console.error('Failed to load quality data:', error)
      setDashboardData({ summary: {}, trend: [] })
      setQualityMetrics([])
    } finally {
      setLoading(false)
    }
  }

  const getAlertStatusTag = (status) => {
    const config = {
      '正常': { color: 'success', icon: <CheckCircleOutlined /> },
      '警告': { color: 'warning', icon: <WarningOutlined /> },
      '告警': { color: 'error', icon: <CloseCircleOutlined /> }
    }
    const cfg = config[status] || config['正常']
    return <Tag color={cfg.color} icon={cfg.icon}>{status}</Tag>
  }

  const trendChartOption = {
    title: {
      text: '数据质量趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['正常交易率', '数据质量率', '综合质量得分'],
      top: 30
    },
    xAxis: {
      type: 'category',
      data: qualityMetrics && qualityMetrics.length > 0 ? qualityMetrics.map(item => item.metric_date).reverse() : []
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
        name: '正常交易率',
        type: 'line',
        data: qualityMetrics && qualityMetrics.length > 0 ? qualityMetrics.map(item => item.normal_rate || 0).reverse() : [],
        smooth: true,
        itemStyle: { color: '#52c41a' }
      },
      {
        name: '数据质量率',
        type: 'line',
        data: qualityMetrics && qualityMetrics.length > 0 ? qualityMetrics.map(item => item.data_quality_rate || 0).reverse() : [],
        smooth: true,
        itemStyle: { color: '#1890ff' }
      },
      {
        name: '综合质量得分',
        type: 'line',
        data: qualityMetrics && qualityMetrics.length > 0 ? qualityMetrics.map(item => item.overall_quality_score || 0).reverse() : [],
        smooth: true,
        itemStyle: { color: '#722ed1' }
      }
    ]
  }

  const dashboardColumns = [
    {
      title: '日期',
      dataIndex: 'transaction_date',
      key: 'transaction_date'
    },
    {
      title: '总交易数',
      dataIndex: 'total_transactions',
      key: 'total_transactions',
      render: (val) => val?.toLocaleString()
    },
    {
      title: '正常交易率',
      dataIndex: 'normal_rate',
      key: 'normal_rate',
      render: (val) => val ? `${val.toFixed(2)}%` : '-'
    },
    {
      title: '数据质量率',
      dataIndex: 'data_quality_rate',
      key: 'data_quality_rate',
      render: (val) => val ? `${val.toFixed(2)}%` : '-'
    },
    {
      title: '告警状态',
      dataIndex: 'alert_status',
      key: 'alert_status',
      render: (status) => getAlertStatusTag(status)
    }
  ]

  if (loading) {
    return <Spin size="large" style={{ display: 'block', textAlign: 'center', marginTop: 100 }} />
  }

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Select value={days} onChange={setDays} style={{ width: 150 }}>
          <Option value={7}>最近7天</Option>
          <Option value={30}>最近30天</Option>
          <Option value={90}>最近90天</Option>
        </Select>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="综合质量得分"
              value={dashboardData.summary?.data_quality_rate || 0}
              precision={2}
              suffix="%"
              valueStyle={{ 
                color: (dashboardData.summary?.data_quality_rate || 0) >= 95 ? '#3f8600' : '#cf1322' 
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="正常交易率"
              value={dashboardData.summary?.normal_rate || 0}
              precision={2}
              suffix="%"
              valueStyle={{ 
                color: (dashboardData.summary?.normal_rate || 0) >= 90 ? '#3f8600' : '#cf1322' 
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总交易数"
              value={dashboardData.summary?.total_transactions || 0}
              formatter={(value) => value.toLocaleString()}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="告警状态"
              value={dashboardData.summary?.alert_status || '正常'}
              valueStyle={{ 
                color: dashboardData.summary?.alert_status === '正常' ? '#3f8600' : '#cf1322' 
              }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24}>
          <Card title="质量趋势图">
            <ReactECharts option={trendChartOption} style={{ height: 400 }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24}>
          <Card title="质量监控详情">
            <Table
              columns={dashboardColumns}
              dataSource={dashboardData.trend || []}
              rowKey="transaction_date"
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

