import React, { useEffect, useState } from 'react'
import { Table, Input, Select, Tag, Card, Drawer, Descriptions, Spin, Space } from 'antd'
import { SearchOutlined } from '@ant-design/icons'
import api from '../utils/api'

const { Search } = Input
const { Option } = Select

export default function DataCatalog() {
  const [loading, setLoading] = useState(false)
  const [tables, setTables] = useState([])
  const [filteredTables, setFilteredTables] = useState([])
  const [selectedTable, setSelectedTable] = useState(null)
  const [drawerVisible, setDrawerVisible] = useState(false)
  const [filters, setFilters] = useState({
    layer: null,
    business_domain: null,
    owner: null,
    search: ''
  })

  useEffect(() => {
    loadTables()
  }, [])

  useEffect(() => {
    filterTables()
  }, [tables, filters])

  const loadTables = async () => {
    try {
      setLoading(true)
      const data = await api.get('/tables')
      setTables(data)
    } catch (error) {
      console.error('Failed to load tables:', error)
    } finally {
      setLoading(false)
    }
  }

  const filterTables = () => {
    let filtered = [...tables]

    if (filters.layer) {
      filtered = filtered.filter(t => t.data_layer === filters.layer)
    }
    if (filters.business_domain) {
      filtered = filtered.filter(t => t.business_domain === filters.business_domain)
    }
    if (filters.owner) {
      filtered = filtered.filter(t => t.owner === filters.owner)
    }
    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      filtered = filtered.filter(t => 
        (t.table_name && t.table_name.toLowerCase().includes(searchLower)) ||
        (t.table_name_cn && t.table_name_cn.toLowerCase().includes(searchLower)) ||
        (t.table_description && t.table_description.toLowerCase().includes(searchLower))
      )
    }

    setFilteredTables(filtered)
  }

  const handleTableClick = async (record) => {
    try {
      const detail = await api.get(`/tables/${record.schema_name}/${record.table_name}`)
      setSelectedTable(detail)
      setDrawerVisible(true)
    } catch (error) {
      console.error('Failed to load table detail:', error)
    }
  }

  const getLayerColor = (layer) => {
    const colors = {
      staging: 'blue',
      ods: 'green',
      dwd: 'orange',
      dws: 'purple',
      ads: 'red',
      metadata: 'default'
    }
    return colors[layer] || 'default'
  }

  const getAssetLevelColor = (level) => {
    const colors = {
      '核心资产': 'red',
      '应用资产': 'orange',
      '基础资产': 'default'
    }
    return colors[level] || 'default'
  }

  const columns = [
    {
      title: '表名',
      dataIndex: 'table_name_cn',
      key: 'table_name_cn',
      width: 200,
      render: (text, record) => (
        <a onClick={() => handleTableClick(record)}>{text || record.table_name}</a>
      )
    },
    {
      title: '描述',
      dataIndex: 'table_description',
      key: 'table_description',
      ellipsis: true
    },
    {
      title: '数据分层',
      dataIndex: 'data_layer',
      key: 'data_layer',
      width: 100,
      render: (layer) => <Tag color={getLayerColor(layer)}>{layer}</Tag>
    },
    {
      title: '业务域',
      dataIndex: 'business_domain',
      key: 'business_domain',
      width: 120
    },
    {
      title: '负责人',
      dataIndex: 'owner',
      key: 'owner',
      width: 120
    },
    {
      title: '记录数',
      dataIndex: 'record_count',
      key: 'record_count',
      width: 100,
      render: (count) => count ? count.toLocaleString() : '-'
    },
    {
      title: '资产等级',
      dataIndex: 'asset_level',
      key: 'asset_level',
      width: 100,
      render: (level) => level ? <Tag color={getAssetLevelColor(level)}>{level}</Tag> : '-'
    }
  ]

  const uniqueDomains = [...new Set(tables.map(t => t.business_domain))]
  const uniqueOwners = [...new Set(tables.map(t => t.owner))]
  const uniqueLayers = [...new Set(tables.map(t => t.data_layer))]

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Space size="middle" wrap>
          <Search
            placeholder="搜索表名或描述"
            style={{ width: 300 }}
            allowClear
            onSearch={(value) => setFilters({ ...filters, search: value })}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          />
          <Select
            placeholder="数据分层"
            style={{ width: 150 }}
            allowClear
            onChange={(value) => setFilters({ ...filters, layer: value })}
          >
            {uniqueLayers.map(layer => (
              <Option key={layer} value={layer}>{layer}</Option>
            ))}
          </Select>
          <Select
            placeholder="业务域"
            style={{ width: 150 }}
            allowClear
            onChange={(value) => setFilters({ ...filters, business_domain: value })}
          >
            {uniqueDomains.map(domain => (
              <Option key={domain} value={domain}>{domain}</Option>
            ))}
          </Select>
          <Select
            placeholder="负责人"
            style={{ width: 150 }}
            allowClear
            onChange={(value) => setFilters({ ...filters, owner: value })}
          >
            {uniqueOwners.map(owner => (
              <Option key={owner} value={owner}>{owner}</Option>
            ))}
          </Select>
        </Space>
      </Card>

      <Card>
        <Table
          columns={columns}
          dataSource={filteredTables}
          rowKey={(record) => `${record.schema_name}.${record.table_name}`}
          loading={loading}
          pagination={{
            pageSize: 20,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Card>

      <Drawer
        title={selectedTable?.table_name_cn || selectedTable?.table_name}
        placement="right"
        width={600}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {selectedTable && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label="表名">{selectedTable.table_name_cn || selectedTable.table_name}</Descriptions.Item>
            <Descriptions.Item label="Schema">{selectedTable.schema_name}</Descriptions.Item>
            <Descriptions.Item label="描述">{selectedTable.table_description}</Descriptions.Item>
            <Descriptions.Item label="业务域">{selectedTable.business_domain}</Descriptions.Item>
            <Descriptions.Item label="数据源">{selectedTable.data_source}</Descriptions.Item>
            <Descriptions.Item label="更新频率">{selectedTable.update_frequency}</Descriptions.Item>
            <Descriptions.Item label="负责人">{selectedTable.owner}</Descriptions.Item>
            <Descriptions.Item label="数据分层">
              <Tag color={getLayerColor(selectedTable.data_layer)}>{selectedTable.data_layer}</Tag>
            </Descriptions.Item>
            {selectedTable.record_count && (
              <Descriptions.Item label="记录数">{selectedTable.record_count.toLocaleString()}</Descriptions.Item>
            )}
            {selectedTable.asset_level && (
              <Descriptions.Item label="资产等级">
                <Tag color={getAssetLevelColor(selectedTable.asset_level)}>{selectedTable.asset_level}</Tag>
              </Descriptions.Item>
            )}
            {selectedTable.quality_metrics && (
              <>
                <Descriptions.Item label="综合质量得分">
                  {selectedTable.quality_metrics.overall_quality_score?.toFixed(2)}%
                </Descriptions.Item>
                <Descriptions.Item label="正常交易率">
                  {selectedTable.quality_metrics.accuracy_rate?.toFixed(2)}%
                </Descriptions.Item>
              </>
            )}
            {selectedTable.columns && (
              <Descriptions.Item label="字段列表">
                <div style={{ maxHeight: 300, overflow: 'auto' }}>
                  {selectedTable.columns.map((col, idx) => (
                    <div key={idx} style={{ marginBottom: 8 }}>
                      <strong>{col.name_cn || col.name}</strong> ({col.data_type})
                      {col.name_cn && col.name_cn !== col.name && (
                        <span style={{ color: '#999', marginLeft: 8, fontSize: '12px' }}>{col.name}</span>
                      )}
                    </div>
                  ))}
                </div>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Drawer>
    </div>
  )
}

