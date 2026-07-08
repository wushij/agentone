<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, Download, DocumentAdd } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { confirmDelete } from '@/utils/confirm'
import { fetchFiles, uploadFile, deleteFile, type FileItem } from '@/api/admin'
import request from '@/api/request'

const files = ref<FileItem[]>([])
const loading = ref(false)
const uploading = ref(false)
const pendingUploads = ref(0)
const uploadStats = ref({ ok: 0, fail: 0 })

async function loadFiles() {
  loading.value = true
  try {
    const res = await fetchFiles()
    files.value = res.records
  } catch (error) {
    ElMessage.error('加载文件列表失败')
  } finally {
    loading.value = false
  }
}

async function finishBatchIfDone() {
  if (pendingUploads.value > 0) return
  uploading.value = false
  const { ok, fail } = uploadStats.value
  uploadStats.value = { ok: 0, fail: 0 }
  if (ok > 0 && fail === 0) {
    ElMessage.success(ok === 1 ? '上传成功' : `成功上传 ${ok} 个文件`)
  } else if (ok > 0 && fail > 0) {
    ElMessage.warning(`成功 ${ok} 个，失败 ${fail} 个`)
  } else if (fail > 0) {
    ElMessage.error(fail === 1 ? '上传失败' : `${fail} 个文件上传失败`)
  }
  await loadFiles()
}

async function handleUpload(options: { file: File }) {
  if (pendingUploads.value === 0) {
    uploading.value = true
  }
  pendingUploads.value++
  try {
    await uploadFile(options.file)
    uploadStats.value.ok++
  } catch {
    uploadStats.value.fail++
  } finally {
    pendingUploads.value--
    void finishBatchIfDone()
  }
}

async function handleDelete(id: string) {
  try {
    if (!(await confirmDelete('确定要删除此文件吗？删除后将无法恢复，知识库中该文件也将失效。'))) return
    await deleteFile(id)
    ElMessage.success('删除成功')
    await loadFiles()
  } catch {
    ElMessage.error('删除失败')
  }
}

async function handleDownload(file: FileItem) {
  const blob = await request.get(`/files/${file.id}/download`, { responseType: 'blob' })
  const url = URL.createObjectURL(blob as unknown as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = file.name
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(loadFiles)
</script>

<template>
  <div class="view-page">
    <PageHeader title="文件中心" subtitle="上传与管理知识库文件，支持上传 PDF / Word / TXT / Markdown 格式文档。" />

    <el-card shadow="never" class="toolbar-card">
      <el-upload
        drag
        multiple
        action="#"
        :http-request="handleUpload"
        :show-file-list="false"
        :disabled="uploading"
        accept=".pdf,.docx,.doc,.txt,.md"
        class="upload-zone"
      >
        <div class="upload-inner" v-loading="uploading">
          <div class="upload-icon" aria-hidden="true">
            <el-icon :size="28"><DocumentAdd /></el-icon>
          </div>
          <div class="upload-main-text">
            拖拽文件到此处，或 <span class="upload-link">点击上传</span>
          </div>
          <div class="upload-tip-text">
            支持一次选择多个文件；仅支持 PDF / Word / TXT / Markdown，单文件不超过 20MB
          </div>
        </div>
      </el-upload>
    </el-card>

    <el-card v-loading="loading" shadow="hover" class="content-card">
      <el-table
        v-if="files.length"
        :data="files"
        stripe
        border
        highlight-current-row
        header-cell-class-name="table-header-style"
      >
        <el-table-column prop="name" label="文件名" min-width="200" show-overflow-tooltip align="center" />
        <el-table-column prop="type" label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" type="info" round>{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="size" label="大小" width="120" align="center" />
        <el-table-column prop="time" label="上传时间" width="180" align="center" />
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <div class="table-actions">
              <el-button size="small" class="action-btn action-btn--primary" :icon="Download" @click="handleDownload(row)">
                下载
              </el-button>
              <el-button size="small" class="action-btn action-btn--danger" :icon="Delete" @click="handleDelete(row.id)">
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <EmptyState v-else title="暂无知识库文件" description="您还没有上传过任何文档，请使用上方拖拽区上传您的第一份文件。" />
    </el-card>
  </div>
</template>

<style scoped>
.toolbar-card {
  margin-bottom: 24px;
  border-radius: var(--ao-radius-xl);
  overflow: hidden;
  border: 1px solid var(--ao-panel-border) !important;
  background: var(--ao-panel-bg);
  box-shadow: 0 10px 30px var(--ao-panel-shadow);
}

.toolbar-card :deep(.el-card__body) {
  padding: 0 !important;
}

.upload-zone {
  background: transparent;
  border-radius: var(--ao-radius-xl);
  display: block;
}

.upload-zone :deep(.el-upload) {
  width: 100%;
  display: block;
}

.upload-zone :deep(.el-upload-dragger) {
  width: 100%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.45) 0%, rgba(248, 250, 255, 0.3) 100%) !important;
  border: 1.5px dashed var(--ao-panel-border) !important;
  border-radius: var(--ao-radius-xl) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 40px 24px !important;
  backdrop-filter: blur(12px);
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

html.dark .upload-zone :deep(.el-upload-dragger) {
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.45) 0%, rgba(15, 23, 42, 0.25) 100%) !important;
  border-color: rgba(99, 120, 160, 0.18) !important;
}

.upload-zone :deep(.el-upload-dragger:hover) {
  border-color: var(--theme-primary) !important;
  background: var(--theme-primary-muted) !important;
  box-shadow: 0 12px 30px rgba(99, 102, 241, 0.06) !important;
}

.upload-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.upload-icon {
  width: 58px;
  height: 58px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 18px;
  background: var(--ao-panel-btn-bg);
  border: 1px solid var(--ao-panel-border);
  color: var(--theme-primary);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.08);
  transition: all 0.3s ease;
}

.upload-zone :deep(.el-upload-dragger:hover) .upload-icon {
  transform: translateY(-3px);
  border-color: var(--theme-primary);
  box-shadow: 0 8px 18px rgba(99, 102, 241, 0.15);
}


.upload-main-text {
  color: var(--ao-text-primary);
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 8px;
}

.upload-link {
  color: var(--theme-primary);
  font-weight: 700;
  transition: color 0.2s ease;
  cursor: pointer;
  border-bottom: 1.5px solid transparent;
}

.upload-link:hover {
  color: var(--theme-primary-hover);
  border-bottom-color: var(--theme-primary-hover);
}

.upload-tip-text {
  color: var(--ao-text-muted);
  font-size: 12px;
  font-weight: 500;
  margin-top: 4px;
}

.text-center { text-align: center; }
.content-card :deep(.el-card__body) {
  padding: 0 !important;
}
.content-card :deep(.empty-state) {
  padding: 24px;
}


</style>
