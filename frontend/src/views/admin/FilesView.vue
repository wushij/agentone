<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Delete,
  Download,
  DocumentAdd,
  Search,
  Files,
  Document,
  Picture,
  VideoCamera,
  Headset,
  ZoomIn
} from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import TablePagination from '@/components/common/TablePagination.vue'
import { usePagination } from '@/composables/usePagination'
import { confirmDelete } from '@/utils/confirm'
import { fetchFiles, uploadFile, deleteFile, type FileItem } from '@/api/admin'
import { renderMarkdown } from '@/utils/markdown'
import request from '@/api/request'

const files = ref<FileItem[]>([])
const loading = ref(false)
const uploading = ref(false)
const pendingUploads = ref(0)
const uploadStats = ref({ ok: 0, fail: 0 })

const searchKeyword = ref('')
const currentFileType = ref<'all' | 'document' | 'image' | 'video' | 'audio'>('all')

const { page, size, total } = usePagination(10)

// 预览图片与 Markdown / 文档弹窗控制
const previewModalVisible = ref(false)
const previewImageUrl = ref('')
const previewImageTitle = ref('')

const docPreviewModalVisible = ref(false)
const docPreviewTitle = ref('')
const docPreviewContent = ref('')
const docPreviewLoading = ref(false)

const filterTabs = [
  { key: 'all', label: '全部文件', icon: Files },
  { key: 'document', label: '文档', icon: Document },
  { key: 'image', label: '图片', icon: Picture },
  { key: 'video', label: '视频', icon: VideoCamera },
  { key: 'audio', label: '音频', icon: Headset }
] as const

async function loadFiles() {
  loading.value = true
  try {
    const res = await fetchFiles({
      page: page.value,
      size: size.value,
      keyword: searchKeyword.value.trim(),
      file_type: currentFileType.value
    })
    files.value = res.records
    total.value = res.total
  } catch {
    ElMessage.error('加载文件列表失败')
  } finally {
    loading.value = false
  }
}

function handleTabChange(tabKey: 'all' | 'document' | 'image' | 'video' | 'audio') {
  currentFileType.value = tabKey
  page.value = 1
  void loadFiles()
}

function handleSearch() {
  page.value = 1
  void loadFiles()
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
  try {
    const res = await request.get(`/files/${file.id}/download`, { responseType: 'blob' })
    const blobData = (res.data ?? res) as Blob
    const url = URL.createObjectURL(blobData)
    const a = document.createElement('a')
    a.href = url
    a.download = file.name
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch {
    ElMessage.error('下载文件失败')
  }
}

function isImageFile(file: FileItem): boolean {
  const ext = file.name.split('.').pop()?.toLowerCase() || ''
  const imgExts = ['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'svg']
  return imgExts.includes(ext) || file.type.toLowerCase().includes('jpg') || file.type.toLowerCase().includes('png')
}

function isTextDocFile(file: FileItem): boolean {
  const ext = file.name.split('.').pop()?.toLowerCase() || ''
  const docExts = ['md', 'markdown', 'txt', 'csv', 'json', 'log', 'py', 'js', 'ts', 'html', 'css', 'yaml', 'yml', 'xml', 'sql']
  return docExts.includes(ext) || file.type.toLowerCase().includes('md') || file.type.toLowerCase().includes('text')
}

function canPreviewFile(file: FileItem): boolean {
  return isImageFile(file) || isTextDocFile(file)
}

function getFileDownloadUrl(fileId: string): string {
  return `/api/v1/files/${fileId}/download`
}

async function openPreview(file: FileItem) {
  if (isImageFile(file)) {
    openImagePreview(file)
  } else if (isTextDocFile(file)) {
    await openDocPreview(file)
  }
}

function openImagePreview(file: FileItem) {
  previewImageUrl.value = getFileDownloadUrl(file.id)
  previewImageTitle.value = file.name
  previewModalVisible.value = true
}

async function openDocPreview(file: FileItem) {
  docPreviewTitle.value = file.name
  docPreviewLoading.value = true
  docPreviewContent.value = ''
  docPreviewModalVisible.value = true
  try {
    const content = await request.get<string>(`/files/${file.id}/download`, {
      responseType: 'text' as never
    })
    docPreviewContent.value = String(content.data ?? content)
  } catch {
    docPreviewContent.value = '(文件文本内容读取失败)'
    ElMessage.error('无法读取文本预览内容')
  } finally {
    docPreviewLoading.value = false
  }
}

const docPreviewHtml = computed(() => {
  if (!docPreviewContent.value) return ''
  return renderMarkdown(docPreviewContent.value)
})

async function copyDocContent() {
  if (!docPreviewContent.value) return
  try {
    await navigator.clipboard.writeText(docPreviewContent.value)
    ElMessage.success('文本内容已成功复制到剪贴板')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

function getTagType(type: string): '' | 'success' | 'warning' | 'info' | 'danger' {
  const t = type.toLowerCase()
  if (['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'svg'].includes(t)) return 'success'
  if (['pdf', 'doc', 'docx', 'txt', 'md', 'markdown'].includes(t)) return ''
  if (['mp4', 'avi', 'mov', 'mkv', 'webm'].includes(t)) return 'warning'
  if (['mp3', 'wav', 'm4a', 'flac', 'ogg'].includes(t)) return 'danger'
  return 'info'
}

onMounted(loadFiles)
</script>

<template>
  <div class="view-page files-page">
    <PageHeader title="文件中心" subtitle="上传与管理知识库文件，支持多分类检索、精细过滤与实时文件预览。" />

    <!-- 拖拽上传区域 -->
    <el-card shadow="never" class="toolbar-card">
      <el-upload
        drag
        multiple
        action="#"
        :http-request="handleUpload"
        :show-file-list="false"
        :disabled="uploading"
        accept=".pdf,.docx,.doc,.txt,.md,.markdown,.png,.jpg,.jpeg,.webp,.gif,.bmp,.svg,.xlsx,.xls,.mp4,.mp3,.wav,.m4a"
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
            支持一次选择多个文件；包含 PDF / Word / Markdown / 图片 / 音视频，单文件建议不超过 50MB
          </div>
        </div>
      </el-upload>
    </el-card>

    <!-- 筛选与搜索工具栏 -->
    <div class="filter-toolbar ao-card">
      <div class="filter-tabs">
        <button
          v-for="tab in filterTabs"
          :key="tab.key"
          type="button"
          class="filter-tab-btn"
          :class="{ 'is-active': currentFileType === tab.key }"
          @click="handleTabChange(tab.key)"
        >
          <el-icon class="tab-icon"><component :is="tab.icon" /></el-icon>
          <span>{{ tab.label }}</span>
        </button>
      </div>

      <div class="filter-search">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索文件名..."
          clearable
          class="search-input"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 文件列表表格卡片 -->
    <el-card v-loading="loading" shadow="hover" class="content-card">
      <template v-if="files.length">
        <el-table
          :data="files"
          stripe
          border
          highlight-current-row
          header-cell-class-name="table-header-style"
        >
          <!-- 文件名 (带图片缩略图/图标) -->
          <el-table-column label="文件名" min-width="180" show-overflow-tooltip>
            <template #default="{ row }">
              <div class="file-name-cell">
                <div v-if="isImageFile(row)" class="image-thumb-box" @click="openImagePreview(row)">
                  <img :src="getFileDownloadUrl(row.id)" :alt="row.name" class="image-thumb" />
                  <div class="thumb-hover-overlay">
                    <el-icon><ZoomIn /></el-icon>
                  </div>
                </div>
                <div v-else class="file-icon-box">
                  <el-icon class="doc-icon"><Document /></el-icon>
                </div>
                <span class="file-name-text" :title="row.name">{{ row.name }}</span>
              </div>
            </template>
          </el-table-column>

          <!-- 类型 -->
          <el-table-column prop="type" label="类型" width="90" align="center">
            <template #default="{ row }">
              <el-tag size="small" effect="plain" :type="getTagType(row.type)" round>
                {{ row.type.toUpperCase() }}
              </el-tag>
            </template>
          </el-table-column>

          <!-- 大小 -->
          <el-table-column prop="size" label="大小" width="110" align="center" />

          <!-- 上传时间 -->
          <el-table-column prop="time" label="上传时间" width="160" align="center" />

          <!-- 操作栏 -->
          <el-table-column label="操作" width="240" fixed="right" align="center">
            <template #default="{ row }">
              <div class="table-actions">
                <el-button
                  v-if="canPreviewFile(row)"
                  size="small"
                  class="action-btn action-btn--neutral"
                  :icon="ZoomIn"
                  @click="openPreview(row)"
                >
                  预览
                </el-button>
                <el-button
                  size="small"
                  class="action-btn action-btn--primary"
                  :icon="Download"
                  @click="handleDownload(row)"
                >
                  下载
                </el-button>
                <el-button
                  size="small"
                  class="action-btn action-btn--danger"
                  :icon="Delete"
                  @click="handleDelete(row.id)"
                >
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-wrapper">
          <TablePagination v-model:page="page" v-model:size="size" :total="total" @change="loadFiles" />
        </div>
      </template>

      <EmptyState
        v-else
        title="暂无相关文件"
        description="未找到符合条件的文件，您可以使用上方拖拽区上传新文件。"
      />
    </el-card>

    <!-- 图片大图预览弹窗 -->
    <el-dialog
      v-model="previewModalVisible"
      :title="previewImageTitle"
      width="720px"
      align-center
      destroy-on-close
      class="image-preview-dialog"
    >
      <div class="image-preview-container">
        <img :src="previewImageUrl" :alt="previewImageTitle" class="preview-full-img" />
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="previewModalVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- Markdown / 文本文档预览弹窗 -->
    <el-dialog
      v-model="docPreviewModalVisible"
      :title="`文件预览 · ${docPreviewTitle}`"
      width="760px"
      align-center
      destroy-on-close
      class="doc-preview-dialog"
    >
      <div v-loading="docPreviewLoading" class="doc-preview-container">
        <div v-if="docPreviewHtml" class="chat-markdown doc-markdown" v-html="docPreviewHtml" />
        <div v-else-if="!docPreviewLoading" class="doc-preview-empty">（暂无预览文本内容）</div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <button
            v-if="docPreviewContent"
            type="button"
            class="btn-copy-report"
            @click="copyDocContent"
          >
            <el-icon><CopyDocument /></el-icon>
            <span>复制内容</span>
          </button>
          <button
            type="button"
            class="btn-close-dialog"
            @click="docPreviewModalVisible = false"
          >
            关闭
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.files-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.toolbar-card {
  margin-bottom: 0;
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
  padding: 32px 24px !important;
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
  width: 52px;
  height: 52px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
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
  margin-bottom: 6px;
}

.upload-link {
  color: var(--theme-primary);
  font-weight: 700;
  cursor: pointer;
}

.upload-tip-text {
  color: var(--ao-text-muted);
  font-size: 12px;
  font-weight: 500;
}

/* 筛选工具栏 */
.filter-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 18px;
  border-radius: 18px;
  background: var(--ao-panel-bg);
  border: 1px solid var(--ao-panel-border);
  flex-wrap: wrap;
}

.filter-tabs {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.filter-tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--ao-text-muted);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-tab-btn:hover {
  background: rgba(99, 102, 241, 0.06);
  color: var(--ao-text-primary);
}

.filter-tab-btn.is-active {
  background: rgba(99, 102, 241, 0.12);
  color: #6366f1;
  border-color: rgba(99, 102, 241, 0.25);
}

.tab-icon {
  font-size: 14px;
}

.filter-search {
  width: min(240px, 100%);
}

.search-input :deep(.el-input__wrapper) {
  border-radius: 999px !important;
  box-shadow: 0 0 0 1px var(--ao-border) inset !important;
}

/* 表格与元素 */
.content-card {
  border-radius: 20px;
}

.content-card :deep(.el-card__body) {
  padding: 0 !important;
}

.file-name-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 2px 0;
}

.image-thumb-box {
  position: relative;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  cursor: pointer;
  border: 1px solid var(--ao-border, rgba(0, 0, 0, 0.1));
}

.image-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumb-hover-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.image-thumb-box:hover .thumb-hover-overlay {
  opacity: 1;
}

.file-icon-box {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: rgba(99, 102, 241, 0.08);
  color: #6366f1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  flex-shrink: 0;
}

.file-name-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--ao-text-primary);
  line-height: 1.4;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.table-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  flex-wrap: nowrap;
  white-space: nowrap;
}

.table-actions .action-btn {
  margin: 0 !important;
  padding: 0 10px !important;
}

.pagination-wrapper {
  padding: 16px;
  display: flex;
  justify-content: flex-start;
}

.image-preview-container {
  display: flex;
  justify-content: center;
  align-items: center;
  max-height: 520px;
  overflow: hidden;
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.03);
}

.preview-full-img {
  max-width: 100%;
  max-height: 500px;
  object-fit: contain;
  border-radius: 8px;
}

.doc-preview-container {
  max-height: min(520px, 62vh);
  overflow-y: auto;
  padding: 16px;
  background: var(--ao-panel-bg, #ffffff);
  border: 1px solid var(--ao-border, rgba(0, 0, 0, 0.08));
  border-radius: 14px;
}

.doc-markdown {
  font-size: 14px;
  line-height: 1.6;
  color: var(--ao-text-primary);
}

.doc-preview-empty {
  color: var(--ao-text-muted);
  text-align: center;
  padding: 40px 0;
}

.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.btn-copy-report {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 36px;
  line-height: 1;
  box-sizing: border-box;
  margin: 0;
  padding: 0 18px;
  border-radius: 999px;
  border: 1px solid rgba(99, 102, 241, 0.3);
  background: rgba(99, 102, 241, 0.08);
  color: #6366f1 !important;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-copy-report:hover {
  background: #6366f1;
  color: #ffffff !important;
  border-color: #6366f1;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}
.btn-copy-report .el-icon {
  font-size: 14px;
  color: inherit !important;
}
.btn-close-dialog {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  line-height: 1;
  box-sizing: border-box;
  margin: 0;
  padding: 0 18px;
  border-radius: 999px;
  border: 1px solid var(--ao-border, rgba(0, 0, 0, 0.12));
  background: var(--ao-panel-bg, #ffffff);
  color: var(--ao-text-secondary, #475569) !important;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-close-dialog:hover {
  background: rgba(0, 0, 0, 0.04);
  color: var(--ao-text-primary, #0f172a) !important;
}
</style>

<style>
.image-preview-dialog .el-dialog,
.doc-preview-dialog .el-dialog {
  border-radius: 20px !important;
  overflow: hidden !important;
  box-shadow: 0 20px 48px rgba(0, 0, 0, 0.18) !important;
}
</style>
