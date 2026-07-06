<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Edit, Delete, FolderOpened, Document, Cpu, Compass, HelpFilled, Check } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import GlassCard from '@/components/common/GlassCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { confirmDelete } from '@/utils/confirm'
import {
  fetchKnowledge,
  createKnowledge,
  updateKnowledge,
  deleteKnowledge,
  fetchFiles,
  fetchModels,
  type KnowledgeItem,
  type FileItem,
  type ModelItem
} from '@/api/admin'

const items = ref<KnowledgeItem[]>([])
const files = ref<FileItem[]>([])
const models = ref<ModelItem[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const activeTab = ref('basic')

const form = ref<Partial<KnowledgeItem>>({
  id: '',
  name: '',
  description: '',
  fileIds: [],
  chunkSize: 500,
  chunkOverlap: 50,
  embeddingModel: '',
  retrievalMode: 'hybrid',
  topK: 3,
  scoreThreshold: 0.5
})

async function loadData() {
  loading.value = true
  try {
    const [kbRes, fileRes, modelRes] = await Promise.all([
      fetchKnowledge(),
      fetchFiles(),
      fetchModels()
    ])
    items.value = kbRes
    files.value = fileRes
    models.value = modelRes
  } catch (error) {
    ElMessage.error('数据加载失败')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  isEdit.value = false
  activeTab.value = 'basic'
  form.value = {
    id: '',
    name: '',
    description: '',
    fileIds: [],
    chunkSize: 500,
    chunkOverlap: 50,
    embeddingModel: models.value[0]?.name || 'text-embedding-3-small',
    retrievalMode: 'hybrid',
    topK: 3,
    scoreThreshold: 0.5
  }
  dialogVisible.value = true
}

function openEdit(kb: KnowledgeItem) {
  isEdit.value = true
  activeTab.value = 'basic'
  form.value = { ...kb }
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.value.name?.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }
  try {
    if (isEdit.value && form.value.id) {
      await updateKnowledge(form.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await createKnowledge(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    await loadData()
  } catch {
    ElMessage.error('保存失败')
  }
}

async function handleDelete(id: string) {
  try {
    if (!(await confirmDelete('确定要删除这个知识库吗？关联的文档数据将不会被物理删除。'))) return
    await deleteKnowledge(id)
    ElMessage.success('删除成功')
    await loadData()
  } catch {
    ElMessage.error('删除失败')
  }
}

function getFilesForKb(kb: KnowledgeItem): FileItem[] {
  return files.value.filter((f) => kb.fileIds.includes(f.id))
}

onMounted(loadData)
</script>

<template>
  <div class="view-page">
    <PageHeader title="知识库管理" subtitle="基于 Dify/Coze 架构的多仓 RAG 检索模型，支持独立向量配置与混合检索策略。">
      <template #action>
        <el-button type="primary" round :icon="Plus" @click="openCreate">新建知识库</el-button>
      </template>
    </PageHeader>

    <div v-loading="loading">
      <div v-if="items.length" class="kb-grid">
        <GlassCard v-for="kb in items" :key="kb.id" class="kb-card">
          <div class="kb-header">
            <div class="kb-icon">
              <el-icon :size="20"><FolderOpened /></el-icon>
            </div>
            <div class="kb-title">
              <h3>{{ kb.name }}</h3>
              <span class="file-count"><el-icon><Document /></el-icon> {{ kb.fileIds.length }} 个关联文件</span>
            </div>
          </div>

          <p class="kb-desc">{{ kb.description || '暂无描述信息' }}</p>

          <div class="kb-tags">
            <el-tag size="small" effect="plain" type="info" round>Top-K: {{ kb.topK || 3 }}</el-tag>
            <el-tag size="small" effect="plain" type="success" round>匹配阈值: {{ kb.scoreThreshold || 0.5 }}</el-tag>
            <el-tag size="small" effect="plain" type="primary" round>
              {{ kb.retrievalMode === 'hybrid' ? '混合检索' : kb.retrievalMode === 'vector' ? '向量检索' : '全文检索' }}
            </el-tag>
          </div>

          <div class="kb-actions table-actions">
            <el-button size="small" class="action-btn action-btn--primary" :icon="Edit" @click="openEdit(kb)">
              配置参数
            </el-button>
            <el-button size="small" class="action-btn action-btn--danger" :icon="Delete" @click="handleDelete(kb.id)">
              删除
            </el-button>
          </div>
        </GlassCard>
      </div>
      <EmptyState v-else title="暂无知识库" description="点击右上角「新建知识库」创建您的第一个 RAG 知识库。" />
    </div>

    <el-dialog
      v-model="dialogVisible"
      width="760px"
      class="ao-detail-dialog"
      append-to-body
      destroy-on-close
    >
      <template #header>
        <div class="detail-dialog-header">
          <el-icon class="detail-dialog-header__icon"><FolderOpened /></el-icon>
          <span class="detail-dialog-header__title">{{ isEdit ? `编辑知识库 · ${form.name || ''}` : '新建知识库' }}</span>
        </div>
      </template>

      <el-tabs v-model="activeTab" class="kb-dialog-tabs">
        <el-tab-pane label="基础设置" name="basic">
          <el-form label-position="top">
            <el-form-item label="知识库名称" required>
              <el-input v-model="form.name" placeholder="请输入知识库名称，例如：HR考勤规范" />
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入知识库的简要描述..." />
            </el-form-item>
            <el-form-item label="关联文件">
              <el-select
                v-model="form.fileIds"
                multiple
                collapse-tags
                collapse-tags-tooltip
                placeholder="选择要加入此知识库的文件"
                class="w-full"
              >
                <el-option
                  v-for="file in files"
                  :key="file.id"
                  :label="file.name"
                  :value="file.id"
                />
              </el-select>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="索引与检索设置" name="retrieval">
          <el-form label-position="top">
            <div class="param-row">
              <el-form-item label="Embedding 模型" class="flex-1">
                <el-select v-model="form.embeddingModel" placeholder="选择嵌入模型" class="w-full">
                  <el-option
                    v-for="m in models"
                    :key="m.name"
                    :label="m.name"
                    :value="m.name"
                  />
                  <el-option label="text-embedding-3-small" value="text-embedding-3-small" />
                </el-select>
              </el-form-item>
              <el-form-item label="切片大小 (Chunk)" class="flex-1">
                <el-input-number v-model="form.chunkSize" :min="100" :max="2000" :step="100" class="w-full" />
              </el-form-item>
            </div>

            <el-form-item label="检索模式">
              <div class="retrieval-cards">
                <div
                  class="retrieval-card"
                  :class="{ active: form.retrievalMode === 'hybrid' }"
                  @click="form.retrievalMode = 'hybrid'"
                >
                  <el-icon><Compass /></el-icon>
                  <div class="card-text">
                    <h4>混合检索 (Hybrid)</h4>
                    <p>同时进行向量检索与全文全文匹配，重排序融合推荐。</p>
                  </div>
                  <div class="check-mark" v-if="form.retrievalMode === 'hybrid'"><el-icon><Check /></el-icon></div>
                </div>

                <div
                  class="retrieval-card"
                  :class="{ active: form.retrievalMode === 'vector' }"
                  @click="form.retrievalMode = 'vector'"
                >
                  <el-icon><Cpu /></el-icon>
                  <div class="card-text">
                    <h4>向量检索 (Vector)</h4>
                    <p>通过嵌入向量提取语义相关度，适合语义模糊查询。</p>
                  </div>
                  <div class="check-mark" v-if="form.retrievalMode === 'vector'"><el-icon><Check /></el-icon></div>
                </div>

                <div
                  class="retrieval-card"
                  :class="{ active: form.retrievalMode === 'fulltext' }"
                  @click="form.retrievalMode = 'fulltext'"
                >
                  <el-icon><HelpFilled /></el-icon>
                  <div class="card-text">
                    <h4>全文检索 (Full-text)</h4>
                    <p>通过关键词匹配进行传统 BM25 检索，适合精确定位名词。</p>
                  </div>
                  <div class="check-mark" v-if="form.retrievalMode === 'fulltext'"><el-icon><Check /></el-icon></div>
                </div>
              </div>
            </el-form-item>

            <div class="param-row">
              <el-form-item label="Top-K 数量" class="flex-1">
                <el-slider v-model="form.topK" :min="1" :max="10" show-input />
              </el-form-item>
              <el-form-item label="相似度得分阈值" class="flex-1">
                <el-slider v-model="form.scoreThreshold" :min="0.1" :max="1.0" :step="0.05" show-input />
              </el-form-item>
            </div>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="文档列表" name="documents" v-if="isEdit && form.fileIds?.length">
          <el-table
            :data="getFilesForKb(form as KnowledgeItem)"
            stripe
            border
            highlight-current-row
            max-height="300"
            header-cell-class-name="table-header-style"
          >
            <el-table-column prop="name" label="文件名" show-overflow-tooltip align="center" />
            <el-table-column prop="type" label="格式" width="100" align="center">
              <template #default="{ row }">
                <el-tag size="small" type="info" round>{{ row.type }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="索引状态" width="120" align="center">
              <template #default>
                <el-tag size="small" type="success" round>已就绪</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <div class="detail-dialog-footer">
          <el-button class="detail-dialog-footer__cancel" @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" class="detail-dialog-footer__submit" @click="handleSave">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.kb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 20px;
}
.kb-card {
  padding: 24px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 240px;
}
.kb-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}
.kb-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--ao-radius-lg);
  background: var(--theme-primary-muted);
  color: var(--theme-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.kb-title h3 {
  margin: 0 0 2px;
  font-size: 15px;
  font-weight: 800;
  color: var(--ao-text-primary);
}
.file-count {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 700;
  color: var(--ao-text-muted);
}
.kb-desc {
  margin: 0 0 16px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--ao-text-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}
.kb-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 18px;
}
.kb-actions {
  display: flex;
  justify-content: space-between;
  border-top: 1px solid var(--ao-border);
  padding-top: 14px;
}
.param-row {
  display: flex;
  gap: 16px;
}
.w-full {
  width: 100%;
}
.flex-1 {
  flex: 1;
}
.kb-dialog-tabs :deep(.el-tabs__item) {
  font-weight: 700;
}
.retrieval-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}
.retrieval-card {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--ao-border);
  border-radius: var(--ao-radius-lg);
  background: var(--ao-surface-muted);
  cursor: pointer;
  transition: all 0.25s ease;
}
.retrieval-card:hover {
  background: var(--ao-surface);
  border-color: var(--theme-primary-muted);
}
.retrieval-card.active {
  border-color: var(--theme-primary);
  background: var(--theme-primary-muted);
}
.retrieval-card .el-icon {
  font-size: 20px;
  color: var(--ao-text-secondary);
  margin-top: 2px;
}
.retrieval-card.active .el-icon {
  color: var(--theme-primary);
}
.card-text h4 {
  margin: 0 0 4px;
  font-size: 13.5px;
  font-weight: 800;
  color: var(--ao-text-primary);
}
.card-text p {
  margin: 0;
  font-size: 11px;
  line-height: 1.5;
  color: var(--ao-text-muted);
}
.check-mark {
  position: absolute;
  top: 14px;
  right: 16px;
  color: var(--theme-primary);
  font-size: 16px;
}
</style>
