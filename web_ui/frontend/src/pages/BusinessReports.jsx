import React, { useEffect, useState } from 'react'
import { Card, Tabs, Table, Select, Row, Col, Statistic } from 'antd'
import ReactECharts from 'echarts-for-react'
import api from '../utils/api'

const { Option } = Select

export default function BusinessReports() {
  const [revenueData, setRevenueData] = useState([])
  const [trafficData, setTrafficData] = useState([])
  const [days, setDays] = useState(30)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadData()
  }, [days])

  const loadData = async () => {
    try {
      setLoading(true)
      const [revenue, traffic] = await Promise.all([
        api.get(`/reports/revenue?days=${days}`),
        api.get(`/reports/traffic?days=${days}`)
      ])
      console.log('Reports data loaded:', { revenue: revenue?.length, traffic: traffic?.length })
      setRevenueData(revenue || [])
      setTrafficData(traffic || [])
    } catch (error) {
      console.error('Failed to load reports:', error)
      setRevenueData([])
      setTrafficData([])
    } finally {
      setLoading(false)
    }
  }

  const revenueChartOption = {
    title: {
      text: '收费收入趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: revenueData && revenueData.length > 0 ? revenueData.map(item => item.transaction_date).reverse() : []
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value} 元'
      }
    },
    series: [
      {
        name: '日收入',
        type: 'bar',
        data: revenueData && revenueData.length > 0 ? revenueData.map(item => item.daily_revenue || 0).reverse() : [],
        itemStyle: { color: '#1890ff' }
      }
    ]
  }

  const trafficChartOption = {
    title: {
      text: '车流趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['日车流量', '唯一车辆数'],
      top: 30
    },
    xAxis: {
      type: 'category',
      data: trafficData && trafficData.length > 0 ? trafficData.map(item => item.transaction_date).reverse() : []
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '日车流量',
        type: 'line',
        data: trafficData && trafficData.length > 0 ? trafficData.map(item => item.daily_vehicles || 0).reverse() : [],
        smooth: true,
        itemStyle: { color: '#52c41a' }
      },
      {
        name: '唯一车辆数',
        type: 'line',
        data: trafficData && trafficData.length > 0 ? trafficData.map(item => item.daily_unique_vehicles || 0).reverse() : [],
        smooth: true,
        itemStyle: { color: '#1890ff' }
      }
    ]
  }

  const revenueColumns = [
    {
      title: '日期',
      dataIndex: 'transaction_date',
      key: 'transaction_date'
    },
    {
      title: '日收入（元）',
      dataIndex: 'daily_revenue',
      key: 'daily_revenue',
      render: (val) => val?.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    },
    {
      title: '日交易数',
      dataIndex: 'daily_transactions',
      key: 'daily_transactions',
      render: (val) => val?.toLocaleString()
    },
    {
      title: '日车辆数',
      dataIndex: 'daily_vehicles',
      key: 'daily_vehicles',
      render: (val) => val?.toLocaleString()
    },
    {
      title: '正常交易率',
      dataIndex: 'normal_rate',
      key: 'normal_rate',
      render: (val) => val ? `${val.toFixed(2)}%` : '-'
    }
  ]

  const trafficColumns = [
    {
      title: '日期',
      dataIndex: 'transaction_date',
      key: 'transaction_date'
    },
    {
      title: '日车流量',
      dataIndex: 'daily_vehicles',
      key: 'daily_vehicles',
      render: (val) => val?.toLocaleString()
    },
    {
      title: '唯一车辆数',
      dataIndex: 'daily_unique_vehicles',
      key: 'daily_unique_vehicles',
      render: (val) => val?.toLocaleString()
    },
    {
      title: 'ETC使用率',
      dataIndex: 'etc_usage_rate',
      key: 'etc_usage_rate',
      render: (val) => val ? `${val.toFixed(2)}%` : '-'
    },
    {
      title: '平均通行时长（分钟）',
      dataIndex: 'avg_travel_minutes',
      key: 'avg_travel_minutes',
      render: (val) => val ? val.toFixed(2) : '-'
    }
  ]

  const totalRevenue = revenueData && revenueData.length > 0 ? revenueData.reduce((sum, item) => sum + (item.daily_revenue || 0), 0) : 0
  const totalTransactions = revenueData && revenueData.length > 0 ? revenueData.reduce((sum, item) => sum + (item.daily_transactions || 0), 0) : 0
  const avgRevenue = revenueData && revenueData.length > 0 ? totalRevenue / revenueData.length : 0

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Select value={days} onChange={setDays} style={{ width: 150 }}>
          <Option value={7}>最近7天</Option>
          <Option value={30}>最近30天</Option>
          <Option value={90}>最近90天</Option>
        </Select>
      </Card>

      <Tabs 
        defaultActiveKey="revenue"
        items={[
          {
            key: 'revenue',
            label: '收费收入报表',
            children: (
              <div>
          <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
            <Col xs={24} sm={8}>
              <Card>
                <Statistic
                  title="总收入"
                  value={totalRevenue}
                  precision={2}
                  suffix="元"
                  formatter={(value) => value.toLocaleString('zh-CN')}
                />
              </Card>
            </Col>
            <Col xs={24} sm={8}>
              <Card>
                <Statistic
                  title="总交易数"
                  value={totalTransactions}
                  formatter={(value) => value.toLocaleString()}
                />
              </Card>
            </Col>
            <Col xs={24} sm={8}>
              <Card>
                <Statistic
                  title="日均收入"
                  value={avgRevenue}
                  precision={2}
                  suffix="元"
                  formatter={(value) => value.toLocaleString('zh-CN')}
                />
              </Card>
            </Col>
          </Row>

          <Card title="收入趋势图" style={{ marginBottom: 16 }}>
            <ReactECharts option={revenueChartOption} style={{ height: 400 }} />
          </Card>

          <Card title="收入明细">
            <Table
              columns={revenueColumns}
              dataSource={revenueData}
              rowKey="transaction_date"
              loading={loading}
              pagination={{ pageSize: 10 }}
            />
          </Card>
              </div>
            )
          },
          {
            key: 'traffic',
            label: '车流趋势分析',
            children: (
              <div>
          <Card title="车流趋势图" style={{ marginBottom: 16 }}>
            <ReactECharts option={trafficChartOption} style={{ height: 400 }} />
          </Card>

          <Card title="车流明细">
            <Table
              columns={trafficColumns}
              dataSource={trafficData}
              rowKey="transaction_date"
              loading={loading}
              pagination={{ pageSize: 10 }}
            />
          </Card>
              </div>
            )
          }
        ]}
      />
    </div>
  )
}

