<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Connection, Plus, Cpu } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import GlassCard from '@/components/common/GlassCard.vue'
import { confirmAction, confirmDelete } from '@/utils/confirm'
import {
  createModel,
  deleteModel,
  fetchModels,
  setDefaultModel,
  testModel,
  updateModel,
  type ModelItem
} from '@/api/admin'

const models = ref<ModelItem[]>([])
const dialog = ref(false)
const editing = ref<ModelItem | null>(null)
const testResults = ref<Record<string, { success: boolean; latency?: number; error?: string }>>({})
const testingModels = ref<Record<string, boolean>>({})

const PROVIDER_DEFAULTS = {
  deepseek: {
    modelName: 'deepseek-v4-flash',
    baseUrl: 'https://api.deepseek.com',
    portalUrl: 'https://platform.deepseek.com'
  },
  openai: {
    modelName: 'gpt-4o',
    baseUrl: 'https://api.openai.com/v1',
    portalUrl: 'https://platform.openai.com'
  },
  qwen: {
    modelName: 'qwen-plus',
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    portalUrl: 'https://modelstudio.console.alibabacloud.com'
  },
  mock: {
    modelName: 'mock-chat',
    baseUrl: '',
    portalUrl: ''
  }
}

const form = reactive({
  name: '',
  provider: '',
  modelName: '',
  baseUrl: '',
  apiKey: '',
  temperature: 0.7,
  isDefault: false
})

onMounted(load)

async function load() {
  models.value = await fetchModels()
}

function openCreate() {
  editing.value = null
  Object.assign(form, {
    name: '',
    provider: '',
    modelName: '',
    baseUrl: '',
    apiKey: '',
    temperature: 0.7,
    isDefault: false
  })
  dialog.value = true
}

function handleProviderChange(val: string) {
  const defaults = PROVIDER_DEFAULTS[val as keyof typeof PROVIDER_DEFAULTS]
  if (!defaults) return
  form.modelName = defaults.modelName
  form.baseUrl = defaults.baseUrl
  if (!editing.value) {
    form.name = defaults.modelName
  }
}

function openEdit(m: ModelItem) {
  editing.value = m
  Object.assign(form, {
    name: m.name,
    provider: m.provider,
    modelName: m.modelName,
    baseUrl: m.baseUrl || '',
    apiKey: '',
    temperature: m.temperature,
    isDefault: m.isDefault
  })
  dialog.value = true
}

async function save() {
  if (!form.name || !form.modelName) {
    ElMessage.warning('请填写完整')
    return
  }
  if (editing.value) {
    await updateModel(editing.value.name, {
      provider: form.provider,
      modelName: form.modelName,
      baseUrl: form.baseUrl || undefined,
      apiKey: form.apiKey || undefined,
      temperature: form.temperature,
      isDefault: form.isDefault
    })
    ElMessage.success('已更新')
  } else {
    await createModel({ ...form })
    ElMessage.success('已创建')
  }
  dialog.value = false
  await load()
}

async function handleTest(name: string) {
  testingModels.value[name] = true
  try {
    const res = await testModel(name)
    testResults.value[name] = { success: true, latency: res.latencyMs }
    ElMessage.success(`连接成功 (${res.latencyMs}ms)`)
  } catch (err: any) {
    const msg = err.response?.data?.message || err.message || '连接失败'
    testResults.value[name] = { success: false, error: msg }
    ElMessage.error(msg)
  } finally {
    testingModels.value[name] = false
  }
}

async function handleDefault(name: string) {
  const ok = await confirmAction({
    message: `确定将「${name}」设为默认模型吗？`,
    confirmButtonText: '设为默认'
  })
  if (!ok) return

  await setDefaultModel(name)
  ElMessage.success('已设为默认模型')
  await load()
}

async function handleDelete(name: string) {
  try {
    if (!(await confirmDelete(`确定删除模型 ${name}？`))) return false
    await deleteModel(name)
    ElMessage.success('已删除')
    await load()
  } catch {
    ElMessage.error('删除失败')
    return false
  }
}
</script>

<template>
  <div class="view-page">
    <PageHeader title="模型管理" subtitle="LLM 接入与参数配置，保存后立即生效">
      <template #action>
        <el-button type="primary" round @click="openCreate"><el-icon><Plus /></el-icon> 新增模型</el-button>
      </template>
    </PageHeader>
    <div class="model-grid">
      <GlassCard v-for="m in models" :key="m.name" class="model-card">
        <div class="model-card__head">
          <h3>{{ m.name }}</h3>
          <el-tag v-if="m.isDefault" type="primary" round size="small">默认</el-tag>
        </div>
        <p class="model-card__provider">{{ m.provider }} · {{ m.modelName }}</p>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <el-tag :type="m.status === 'enabled' ? 'success' : 'info'" round>{{ m.status }}</el-tag>
          <span v-if="testResults[m.name]" :style="{ color: testResults[m.name].success ? 'var(--el-color-success)' : 'var(--el-color-danger)', fontSize: '13px' }">
            {{ testResults[m.name].success ? `连接成功 (${testResults[m.name].latency}ms)` : '连接失败' }}
          </span>
        </div>
        <div class="model-card__actions">
          <el-button size="small" class="action-btn action-btn--neutral" :icon="Connection" :loading="testingModels[m.name]" @click="handleTest(m.name)">
            测试
          </el-button>
          <el-button size="small" class="action-btn action-btn--edit" @click="openEdit(m)">编辑</el-button>
          <el-button
            v-if="!m.isDefault"
            size="small"
            class="action-btn action-btn--primary"
            @click="handleDefault(m.name)"
          >
            设默认
          </el-button>
          <el-button size="small" class="action-btn action-btn--danger" @click="handleDelete(m.name)">删除</el-button>
        </div>
      </GlassCard>
    </div>

    <el-dialog
      v-model="dialog"
      width="520px"
      class="ao-detail-dialog"
      append-to-body
      destroy-on-close
    >
      <template #header>
        <div class="detail-dialog-header">
          <el-icon class="detail-dialog-header__icon"><Cpu /></el-icon>
          <span class="detail-dialog-header__title">{{ editing ? '编辑模型' : '新增模型' }}</span>
        </div>
      </template>

      <el-form label-width="100px">
        <el-form-item label="名称"><el-input v-model="form.name" :disabled="!!editing" /></el-form-item>
        <el-form-item label="供应商">
          <el-select v-model="form.provider" placeholder="请选择供应商" style="width: 100%" @change="handleProviderChange">
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="OpenAI" value="openai" />
            <el-option label="Qwen" value="qwen" />
            <el-option label="Mock" value="mock" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型名称"><el-input v-model="form.modelName" /></el-form-item>
        <el-form-item label="请求地址"><el-input v-model="form.baseUrl" placeholder="可选" /></el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="form.apiKey" type="password" show-password :placeholder="editing?.hasApiKey ? '留空不修改' : ''" />
          <el-link
            v-if="form.provider && PROVIDER_DEFAULTS[form.provider as keyof typeof PROVIDER_DEFAULTS]?.portalUrl"
            type="primary"
            :href="PROVIDER_DEFAULTS[form.provider as keyof typeof PROVIDER_DEFAULTS].portalUrl"
            target="_blank"
            style="margin-top: 4px; font-size: 12px;"
          >
            获取 {{ form.provider === 'deepseek' ? 'deepseek' : (form.provider === 'openai' ? 'OpenAI' : (form.provider === 'qwen' ? 'Qwen' : 'Mock')) }} API Key
          </el-link>
        </el-form-item>
        <el-form-item label="Temperature"><el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" /></el-form-item>
        <el-form-item label="默认模型"><el-switch v-model="form.isDefault" /></el-form-item>
      </el-form>
      <template #footer>
        <div class="detail-dialog-footer">
          <el-button class="detail-dialog-footer__cancel" @click="dialog = false">取消</el-button>
          <el-button type="primary" class="detail-dialog-footer__submit" @click="save">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.model-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
}

.model-card__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.model-card__head h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}

.model-card__provider {
  color: var(--ao-text-muted);
  font-size: 13px;
  margin: 0 0 12px;
}

.model-card__actions {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
}

.model-card__actions .action-btn {
  flex-shrink: 0;
  white-space: nowrap;
}
</style>