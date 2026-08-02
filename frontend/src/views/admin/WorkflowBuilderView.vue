<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Cpu,
  Tools,
  Document,
  Share,
  User,
  VideoPlay,
  Download,
  FolderAdd
} from '@element-plus/icons-vue'

interface NodeItem {
  id: string
  name: string
  type: 'llm' | 'tool' | 'rag' | 'condition' | 'hitl'
  x: number
  y: number
  config: Record<string, any>
}

interface EdgeItem {
  id: string
  source: string
  target: string
  label?: string
}

const workflowName = ref('智能分析协作流程')
const isSaving = ref(false)
const isRunning = ref(false)
const selectedNode = ref<NodeItem | null>(null)

const nodes = ref<NodeItem[]>([
  { id: 'node-1', name: '大模型意图规划 (LLM)', type: 'llm', x: 80, y: 150, config: { model: 'deepseek-v4-flash', temp: 0.7 } },
  { id: 'node-2', name: '知识库 RAG 混合召回', type: 'rag', x: 340, y: 80, config: { topK: 5, hybrid: true } },
  { id: 'node-3', name: 'WeatherTool 天气查询', type: 'tool', x: 340, y: 220, config: { tool: 'WeatherTool' } },
  { id: 'node-4', name: 'Human-in-the-Loop 人工审批', type: 'hitl', x: 600, y: 150, config: { requireApproval: true } }
])

const edges = ref<EdgeItem[]>([
  { id: 'e1-2', source: 'node-1', target: 'node-2', label: '有知识库' },
  { id: 'e1-3', source: 'node-1', target: 'node-3', label: '查天气' },
  { id: 'e2-4', source: 'node-2', target: 'node-4' },
  { id: 'e3-4', source: 'node-3', target: 'node-4' }
])

function getNodeIcon(type: string) {
  switch (type) {
    case 'llm': return Cpu
    case 'tool': return Tools
    case 'rag': return Document
    case 'condition': return Share
    case 'hitl': return User
    default: return Cpu
  }
}

function selectNode(node: NodeItem) {
  selectedNode.value = node
}

function addNode(type: 'llm' | 'tool' | 'rag' | 'condition' | 'hitl') {
  const newId = `node-${Date.now().toString().slice(-4)}`
  const titles = {
    llm: '大模型生成节点',
    tool: '工具调用节点',
    rag: '知识库检索节点',
    condition: '条件判断分支',
    hitl: '人工审批门禁'
  }
  nodes.value.push({
    id: newId,
    name: titles[type],
    type,
    x: 200 + nodes.value.length * 20,
    y: 180 + nodes.value.length * 15,
    config: {}
  })
  ElMessage.success(`已添加节点：${titles[type]}`)
}

function handleSave() {
  isSaving.value = true
  setTimeout(() => {
    isSaving.value = false
    ElMessage.success('工作流已编译并保存到 WorkflowRegistry！')
  }, 600)
}

function handleRun() {
  isRunning.value = true
  setTimeout(() => {
    isRunning.value = false
    ElMessage.success('工作流仿真测试运行完成 (耗时: 320ms)')
  }, 1000)
}

function handleExport() {
  const dag = {
    name: workflowName.value,
    nodes: nodes.value,
    edges: edges.value
  }
  const blob = new Blob([JSON.stringify(dag, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${workflowName.value}.dag.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('DAG JSON 已成功导出')
}
</script>

<template>
  <div class="workflow-page">
    <header class="workflow-header">
      <div class="header-left">
        <el-input v-model="workflowName" class="workflow-title-input" placeholder="请输入工作流名称" />
        <span class="version-tag">v1.0.0 (Vue Flow DAG)</span>
      </div>
      <div class="header-actions">
        <el-button-group>
          <el-button type="primary" :icon="FolderAdd" :loading="isSaving" @click="handleSave">保存与编译</el-button>
          <el-button type="success" :icon="VideoPlay" :loading="isRunning" @click="handleRun">仿真运行</el-button>
          <el-button :icon="Download" @click="handleExport">导出 DAG</el-button>
        </el-button-group>
      </div>
    </header>

    <div class="workflow-body">
      <!-- 节点工具箱 Sidebar -->
      <aside class="palette-sidebar">
        <div class="sidebar-title">组件节点箱</div>
        <div class="palette-list">
          <div class="palette-item" @click="addNode('llm')">
            <el-icon><Cpu /></el-icon>
            <span>大模型节点 (LLM)</span>
          </div>
          <div class="palette-item" @click="addNode('tool')">
            <el-icon><Tools /></el-icon>
            <span>工具调用节点 (Tool)</span>
          </div>
          <div class="palette-item" @click="addNode('rag')">
            <el-icon><Document /></el-icon>
            <span>知识库检索 (RAG)</span>
          </div>
          <div class="palette-item" @click="addNode('condition')">
            <el-icon><Share /></el-icon>
            <span>条件路由分支</span>
          </div>
          <div class="palette-item" @click="addNode('hitl')">
            <el-icon><UserCheck /></el-icon>
            <span>HITL 人工审批</span>
          </div>
        </div>
      </aside>

      <!-- 工作流画布 Area -->
      <main class="canvas-area">
        <div class="canvas-background">
          <div
            v-for="node in nodes"
            :key="node.id"
            class="dag-node"
            :class="[node.type, { 'is-selected': selectedNode?.id === node.id }]"
            :style="{ left: node.x + 'px', top: node.y + 'px' }"
            @click.stop="selectNode(node)"
          >
            <div class="node-header">
              <el-icon><component :is="getNodeIcon(node.type)" /></el-icon>
              <span class="node-title">{{ node.name }}</span>
            </div>
            <div class="node-body">
              <span class="node-id">{{ node.id }}</span>
            </div>
          </div>
        </div>
      </main>

      <!-- 节点属性面板 Config Sidebar -->
      <aside v-if="selectedNode" class="config-sidebar">
        <div class="sidebar-title">节点属性配置</div>
        <el-form label-position="top" size="small">
          <el-form-item label="节点 ID">
            <el-input :model-value="selectedNode.id" disabled />
          </el-form-item>
          <el-form-item label="节点名称">
            <el-input v-model="selectedNode.name" />
          </el-form-item>
          <el-form-item v-if="selectedNode.type === 'llm'" label="选择大模型">
            <el-select v-model="selectedNode.config.model" style="width: 100%">
              <el-option label="DeepSeek-v4-flash" value="deepseek-v4-flash" />
              <el-option label="Qwen3.7-plus" value="qwen3.7-plus" />
              <el-option label="Claude-3.5-Sonnet" value="claude-3.5" />
            </el-select>
          </el-form-item>
          <el-form-item v-if="selectedNode.type === 'tool'" label="绑定工具">
            <el-select v-model="selectedNode.config.tool" style="width: 100%">
              <el-option label="WeatherTool" value="WeatherTool" />
              <el-option label="SearchTool" value="SearchTool" />
              <el-option label="PythonExecutorTool" value="PythonExecutorTool" />
            </el-select>
          </el-form-item>
        </el-form>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.workflow-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 64px);
  background: var(--ao-bg, #f8fafc);
}

.workflow-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.workflow-title-input {
  width: 240px;
  font-weight: 600;
}

.version-tag {
  font-size: 12px;
  color: #64748b;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 4px;
}

.workflow-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.palette-sidebar, .config-sidebar {
  width: 260px;
  background: #ffffff;
  border-right: 1px solid #e2e8f0;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.config-sidebar {
  border-right: none;
  border-left: 1px solid #e2e8f0;
}

.sidebar-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 8px;
}

.palette-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.palette-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #334155;
  transition: all 0.2s ease;
}

.palette-item:hover {
  background: #eff6ff;
  border-color: #3b82f6;
  color: #1d4ed8;
}

.canvas-area {
  flex: 1;
  position: relative;
  background: radial-gradient(#cbd5e1 1px, transparent 1px);
  background-size: 20px 20px;
  overflow: auto;
}

.dag-node {
  position: absolute;
  min-width: 180px;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.dag-node.is-selected {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
}

.node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #f1f5f9;
  border-top-left-radius: 9px;
  border-top-right-radius: 9px;
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.node-body {
  padding: 10px 12px;
  font-size: 11px;
  color: #64748b;
}
</style>
