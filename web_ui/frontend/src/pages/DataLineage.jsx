import React, { useEffect, useState, useRef } from 'react'
import { Card, Spin, Input, Select, Button, Space, Tag, Drawer, Descriptions } from 'antd'
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons'
import CytoscapeComponent from 'react-cytoscapejs'
import cytoscape from 'cytoscape'
import api from '../utils/api'

const { Search } = Input
const { Option } = Select

export default function DataLineage() {
  const [loading, setLoading] = useState(false)
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] })
  const [selectedNode, setSelectedNode] = useState(null)
  const [drawerVisible, setDrawerVisible] = useState(false)
  const [layout, setLayout] = useState('breadthfirst')
  const [searchText, setSearchText] = useState('')

  useEffect(() => {
    loadLineage()
  }, [])

  const loadLineage = async () => {
    try {
      setLoading(true)
      const data = await api.get('/lineage/graph')
      setGraphData(data)
    } catch (error) {
      console.error('Failed to load lineage:', error)
    } finally {
      setLoading(false)
    }
  }

  const getNodeColor = (layer) => {
    const colors = {
      staging: '#1890ff',
      ods: '#52c41a',
      dwd: '#faad14',
      dws: '#722ed1',
      ads: '#f5222d',
      metadata: '#8c8c8c',
      unknown: '#d9d9d9'
    }
    return colors[layer] || colors.unknown
  }

  const getEdgeColor = (type) => {
    const colors = {
      '清洗': '#1890ff',
      '关联': '#52c41a',
      '转换': '#faad14',
      '汇总': '#722ed1',
      '聚合': '#f5222d'
    }
    return colors[type] || '#8c8c8c'
  }

  const cyElements = [
    ...graphData.nodes.map(node => ({
      data: {
        id: node.id,
        label: node.label,
        layer: node.layer,
        full_name: node.full_name
      },
      style: {
        backgroundColor: getNodeColor(node.layer),
        label: node.label,
        width: 80,
        height: 80,
        shape: 'roundrectangle',
        'text-valign': 'center',
        'text-halign': 'center',
        color: '#fff',
        'font-size': 12,
        'font-weight': 'bold'
      }
    })),
    ...graphData.edges.map(edge => ({
      data: {
        source: edge.source,
        target: edge.target,
        type: edge.type,
        description: edge.description
      },
      style: {
        width: 2,
        'line-color': getEdgeColor(edge.type),
        'target-arrow-color': getEdgeColor(edge.type),
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'arrow-scale': 1.5
      }
    }))
  ]

  const handleNodeClick = async (evt) => {
    const nodeData = evt.target.data()
    if (nodeData.id) {
      const [schema, table] = nodeData.full_name.split('.')
      try {
        const detail = await api.get(`/tables/${schema}/${table}`)
        setSelectedNode({ ...detail, ...nodeData })
        setDrawerVisible(true)
      } catch (error) {
        console.error('Failed to load node detail:', error)
      }
    }
  }

  const layoutOptions = {
    name: layout,
    spacingFactor: 1.5,
    animate: true,
    animationDuration: 1000
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

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Space>
          <Search
            placeholder="搜索表名"
            style={{ width: 300 }}
            onSearch={(value) => setSearchText(value)}
            allowClear
          />
          <Select
            value={layout}
            onChange={setLayout}
            style={{ width: 150 }}
          >
            <Option value="breadthfirst">广度优先</Option>
            <Option value="grid">网格</Option>
            <Option value="circle">圆形</Option>
            <Option value="concentric">同心圆</Option>
            <Option value="cose">力导向</Option>
          </Select>
          <Button icon={<ReloadOutlined />} onClick={loadLineage}>刷新</Button>
        </Space>
      </Card>

      <Card>
        <div style={{ height: '70vh', border: '1px solid #f0f0f0', borderRadius: 4 }}>
          {loading ? (
            <Spin size="large" style={{ display: 'block', textAlign: 'center', marginTop: '30vh' }} />
          ) : (
            <CytoscapeComponent
              elements={cyElements}
              style={{ width: '100%', height: '100%' }}
              layout={layoutOptions}
              cy={(cy) => {
                cy.on('tap', 'node', handleNodeClick)
                cy.fit()
              }}
            />
          )}
        </div>
      </Card>

      <Card style={{ marginTop: 16 }}>
        <h3>图例</h3>
        <Space wrap>
          <Tag color="blue">Staging</Tag>
          <Tag color="green">ODS</Tag>
          <Tag color="orange">DWD</Tag>
          <Tag color="purple">DWS</Tag>
          <Tag color="red">ADS</Tag>
          <Tag>Metadata</Tag>
        </Space>
        <div style={{ marginTop: 16 }}>
          <h4>转换类型：</h4>
          <Space wrap>
            <Tag color="blue">清洗</Tag>
            <Tag color="green">关联</Tag>
            <Tag color="orange">转换</Tag>
            <Tag color="purple">汇总</Tag>
            <Tag color="red">聚合</Tag>
          </Space>
        </div>
      </Card>

      <Drawer
        title={selectedNode?.table_name_cn || selectedNode?.table_name}
        placement="right"
        width={600}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {selectedNode && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label="表名">{selectedNode.table_name_cn || selectedNode.table_name}</Descriptions.Item>
            <Descriptions.Item label="Schema">{selectedNode.schema_name}</Descriptions.Item>
            <Descriptions.Item label="描述">{selectedNode.table_description}</Descriptions.Item>
            <Descriptions.Item label="数据分层">
              <Tag color={getLayerColor(selectedNode.data_layer)}>{selectedNode.data_layer}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="业务域">{selectedNode.business_domain}</Descriptions.Item>
            <Descriptions.Item label="负责人">{selectedNode.owner}</Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>
    </div>
  )
}

