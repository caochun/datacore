import React, { useEffect, useState } from 'react'
import { Card, Select, Table, Descriptions, Tag, Spin, Space, Button } from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import api from '../utils/api'

const { Option } = Select

export default function DataExplorer() {
  const [loading, setLoading] = useState(false)
  const [tables, setTables] = useState([])
  const [selectedTable, setSelectedTable] = useState(null)
  const [tableData, setTableData] = useState({ columns: [], data: [], total: 0 })
  const [pagination, setPagination] = useState({ current: 1, pageSize: 100 })

  useEffect(() => {
    loadTables()
  }, [])

  useEffect(() => {
    if (selectedTable) {
      loadTableData()
    }
  }, [selectedTable, pagination])

  const loadTables = async () => {
    try {
      const data = await api.get('/tables')
      setTables(data)
      if (data.length > 0 && !selectedTable) {
        setSelectedTable(`${data[0].schema_name}.${data[0].table_name}`)
      }
    } catch (error) {
      console.error('Failed to load tables:', error)
    }
  }

  const loadTableData = async () => {
    if (!selectedTable) return
    
    try {
      setLoading(true)
      const [schema, table] = selectedTable.split('.')
      const offset = (pagination.current - 1) * pagination.pageSize
      const data = await api.get(`/tables/${schema}/${table}/preview`, {
        params: {
          limit: pagination.pageSize,
          offset: offset
        }
      })
      setTableData(data)
    } catch (error) {
      console.error('Failed to load table data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleTableChange = (table) => {
    setSelectedTable(table)
    setPagination({ ...pagination, current: 1 })
  }

  const handleTableChangePage = (page, pageSize) => {
    setPagination({ current: page, pageSize })
  }

  const columns = tableData.columns.map(col => ({
    title: tableData.columns_cn?.[col] || col,
    dataIndex: col,
    key: col,
    ellipsis: true,
    render: (text) => {
      if (text === null || text === undefined) {
        return <Tag color="default">NULL</Tag>
      }
      if (typeof text === 'string' && text.length > 50) {
        return text.substring(0, 50) + '...'
      }
      return String(text)
    }
  }))

  const selectedTableInfo = tables.find(t => 
    `${t.schema_name}.${t.table_name}` === selectedTable
  )

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Space>
          <span>选择数据表：</span>
          <Select
            value={selectedTable}
            onChange={handleTableChange}
            style={{ width: 400 }}
            showSearch
            filterOption={(input, option) =>
              option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
            }
          >
            {tables.map(table => (
              <Option key={`${table.schema_name}.${table.table_name}`} value={`${table.schema_name}.${table.table_name}`}>
                {table.schema_name}.{table.table_name}
              </Option>
            ))}
          </Select>
          <Button icon={<ReloadOutlined />} onClick={loadTableData}>刷新</Button>
        </Space>
      </Card>

      {selectedTableInfo && (
        <Card style={{ marginBottom: 16 }} title="表信息">
          <Descriptions column={3} size="small">
            <Descriptions.Item label="表名">{selectedTableInfo?.table_name_cn || selectedTableInfo?.table_name}</Descriptions.Item>
            <Descriptions.Item label="Schema">{selectedTableInfo?.schema_name}</Descriptions.Item>
            <Descriptions.Item label="业务域">{selectedTableInfo?.business_domain}</Descriptions.Item>
            <Descriptions.Item label="数据分层">
              <Tag>{selectedTableInfo.data_layer}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="记录数">
              {tableData.total.toLocaleString()}
            </Descriptions.Item>
            <Descriptions.Item label="负责人">{selectedTableInfo.owner}</Descriptions.Item>
            <Descriptions.Item label="描述" span={3}>
              {selectedTableInfo.table_description}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      )}

      <Card title="数据预览">
        <Table
          columns={columns}
          dataSource={tableData.data}
          rowKey={(record, index) => index}
          loading={loading}
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: tableData.total,
            showTotal: (total) => `共 ${total.toLocaleString()} 条记录`,
            showSizeChanger: true,
            pageSizeOptions: ['50', '100', '200', '500'],
            onChange: handleTableChangePage,
            onShowSizeChange: handleTableChangePage
          }}
          scroll={{ x: 'max-content', y: 600 }}
        />
      </Card>
    </div>
  )
}

