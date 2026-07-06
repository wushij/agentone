<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import { confirmAction } from '@/utils/confirm'
import { fetchSettings, updateSettings } from '@/api/admin'

const activeTab = ref('basic')
const loading = ref(false)

const form = reactive({
  siteName: 'AgentOne',
  announcement: '',
  defaultModel: 'deepseek-chat',
  defaultTemperature: 0.7,
  maxContext: 8192,
  jwtExpireMinutes: 1440,
  rateLimitEnabled: true,
  rateLimitPerMinute: 120
})

onMounted(async () => {
  loading.value = true
  try {
    const data = await fetchSettings()
    Object.assign(form, {
      siteName: data.siteName ?? form.siteName,
      announcement: data.announcement ?? '',
      defaultModel: data.defaultModel ?? form.defaultModel,
      defaultTemperature: Number(data.defaultTemperature ?? form.defaultTemperature),
      maxContext: Number(data.maxContext ?? form.maxContext),
      jwtExpireMinutes: Number(data.jwtExpireMinutes ?? form.jwtExpireMinutes),
      rateLimitEnabled: data.rateLimitEnabled ?? true,
      rateLimitPerMinute: Number(data.rateLimitPerMinute ?? form.rateLimitPerMinute)
    })
  } finally {
    loading.value = false
  }
})

async function save() {
  const ok = await confirmAction({
    message: '确定要保存系统设置吗？部分配置将立即生效。',
    confirmButtonText: '保存'
  })
  if (!ok) return

  loading.value = true
  try {
    await updateSettings({ ...form })
    ElMessage.success('设置已保存')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="view-page">
    <PageHeader title="系统设置" subtitle="站点信息、AI 参数与安全配置" />

    <el-card v-loading="loading" shadow="hover" class="settings-card content-card">
      <el-tabs v-model="activeTab" class="settings-tabs">
        <el-tab-pane label="基础" name="basic">
          <el-form label-position="top" class="settings-form">
            <el-form-item label="站点名称">
              <el-input v-model="form.siteName" placeholder="显示在浏览器标题与登录页" class="custom-input" />
            </el-form-item>
            <el-form-item label="系统公告">
              <el-input
                v-model="form.announcement"
                type="textarea"
                :rows="4"
                placeholder="可选，展示在首页或登录页的欢迎说明"
                class="custom-textarea"
              />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="AI 参数" name="ai">
          <el-form label-position="top" class="settings-form">
            <div class="form-grid-2">
              <el-form-item label="默认模型">
                <el-input v-model="form.defaultModel" placeholder="如 deepseek-chat" class="custom-input" />
              </el-form-item>
              <el-form-item label="最大上下文">
                <el-input-number v-model="form.maxContext" :min="1024" :max="128000" :step="1024" class="custom-number" />
              </el-form-item>
            </div>
            <el-form-item label="默认温度">
              <el-slider v-model="form.defaultTemperature" :min="0" :max="2" :step="0.1" show-input />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="安全" name="security">
          <el-form label-position="top" class="settings-form">
            <div class="form-grid-2">
              <el-form-item label="JWT 有效期（分钟）">
                <el-input-number v-model="form.jwtExpireMinutes" :min="30" :max="10080" class="custom-number" />
              </el-form-item>
              <el-form-item label="每分钟请求上限">
                <el-input-number
                  v-model="form.rateLimitPerMinute"
                  :min="30"
                  :max="1000"
                  :disabled="!form.rateLimitEnabled"
                  class="custom-number"
                />
              </el-form-item>
            </div>
            <div class="switch-row">
              <div class="switch-row__info">
                <span class="switch-row__title">启用 API 限流</span>
                <span class="switch-row__desc">开启后将对接口请求频率进行限制，防止滥用。</span>
              </div>
              <el-switch v-model="form.rateLimitEnabled" />
            </div>
          </el-form>
        </el-tab-pane>
      </el-tabs>

      <div class="settings-footer">
        <el-button type="primary" class="btn-save" :loading="loading" @click="save">保存设置</el-button>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.settings-card :deep(.el-card__body) {
  padding: 8px 24px 24px !important;
}

.settings-tabs :deep(.el-tabs__header) {
  margin-bottom: 8px;
}

.settings-tabs :deep(.el-tabs__item) {
  height: 44px;
  font-size: 14px;
  font-weight: 600;
}

.settings-form {
  max-width: 640px;
  padding: 12px 4px 0;
}

.settings-form :deep(.el-form-item__label) {
  font-weight: 600;
  font-size: 13px;
  color: var(--ao-text-primary);
  padding-bottom: 8px !important;
}

.form-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.custom-input :deep(.el-input__wrapper) {
  border-radius: 999px !important;
  padding: 6px 18px !important;
  min-height: 40px;
  box-shadow: 0 0 0 1px var(--ao-border) inset !important;
  background: #f8fafc !important;
}

.custom-textarea :deep(.el-textarea__inner) {
  border-radius: 20px !important;
  padding: 14px 18px !important;
  box-shadow: 0 0 0 1px var(--ao-border) inset !important;
  background: #f8fafc !important;
  font-size: 13px;
  line-height: 1.6;
  min-height: 120px;
}

.custom-number {
  width: 100%;
}

.custom-number :deep(.el-input-number) {
  width: 100%;
  border-radius: 999px !important;
  overflow: hidden;
  border: none !important;
  background: #f8fafc !important;
  box-shadow: 0 0 0 1px var(--ao-border) inset !important;
  transition: box-shadow 0.2s ease, background 0.2s ease;
}

.custom-number :deep(.el-input-number:hover) {
  box-shadow: 0 0 0 1px rgba(148, 163, 184, 0.45) inset !important;
}

.custom-number :deep(.el-input-number.is-focus),
.custom-number :deep(.el-input-number:focus-within) {
  background: #fff !important;
  box-shadow: 0 0 0 1px #4f46e5 inset !important;
}

.custom-number :deep(.el-input__wrapper) {
  border-radius: 0 !important;
  padding: 4px 8px !important;
  min-height: 40px;
  box-shadow: none !important;
  background: transparent !important;
  transform: none !important;
}

.custom-number :deep(.el-input__wrapper.is-focus) {
  box-shadow: none !important;
  background: transparent !important;
  transform: none !important;
}

.custom-number :deep(.el-input-number__decrease),
.custom-number :deep(.el-input-number__increase) {
  width: 38px;
  border: none !important;
  border-radius: 0 !important;
  background: transparent !important;
  color: var(--ao-text-secondary);
}

.custom-number :deep(.el-input-number__decrease:hover),
.custom-number :deep(.el-input-number__increase:hover) {
  color: #4f46e5;
  background: rgba(79, 70, 229, 0.06) !important;
}

.custom-input :deep(.el-input__wrapper.is-focus),
.custom-textarea :deep(.el-textarea__inner:focus) {
  background: #fff !important;
  box-shadow: 0 0 0 1px #4f46e5 inset !important;
  transform: none !important;
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 8px;
  padding: 16px 20px;
  border-radius: 20px;
  border: 1px solid var(--ao-border);
  background: #f8fafc;
}

.switch-row__info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.switch-row__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--ao-text-primary);
}

.switch-row__desc {
  font-size: 12px;
  color: var(--ao-text-secondary);
  line-height: 1.5;
}

.settings-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--ao-border);
}

.btn-save {
  border-radius: 999px !important;
  padding: 10px 28px !important;
  height: auto !important;
  font-weight: 600 !important;
  border: none !important;
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 50%, #8b5cf6 100%) !important;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3) !important;
}

.btn-save:hover {
  filter: brightness(1.05);
  box-shadow: 0 6px 18px rgba(99, 102, 241, 0.38) !important;
}

html.dark .custom-number :deep(.el-input-number) {
  background: var(--ao-surface-muted) !important;
  box-shadow: 0 0 0 1px var(--ao-surface-border) inset !important;
}

html.dark .custom-input :deep(.el-input__wrapper),
html.dark .custom-textarea :deep(.el-textarea__inner),
html.dark .switch-row {
  background: var(--ao-surface-muted) !important;
}

@media (max-width: 768px) {
  .form-grid-2 {
    grid-template-columns: 1fr;
  }
}
</style>
