<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, User, Search } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import TablePagination from '@/components/common/TablePagination.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { usePagination } from '@/composables/usePagination'
import { confirmAction, confirmDelete } from '@/utils/confirm'
import {
  createUser,
  deleteUser,
  fetchUsers,
  updateUser,
  type UserItem
} from '@/api/admin'

const users = ref<UserItem[]>([])
const loading = ref(false)
const { page, size, total } = usePagination(10)

const searchKeyword = ref('')
const selectedRole = ref('')
const selectedStatus = ref<string>('all')

const dialog = ref(false)
const editing = ref<UserItem | null>(null)

const form = reactive({
  username: '',
  password: '',
  nickname: '',
  role: 'user',
  status: 1
})

const roleOptions = [
  { label: '普通用户', value: 'user' },
  { label: '管理员', value: 'admin' },
  { label: '超级管理员', value: 'super_admin' }
]

const roleFilterTabs = [
  { key: '', label: '全部角色' },
  { key: 'user', label: '普通用户' },
  { key: 'admin', label: '管理员' },
  { key: 'super_admin', label: '超级管理员' }
]

const statusFilterOptions = [
  { label: '全部状态', value: 'all' },
  { label: '正常', value: '1' },
  { label: '禁用', value: '0' }
]

async function load() {
  loading.value = true
  try {
    let statusParam: number | undefined = undefined
    if (selectedStatus.value === '1') statusParam = 1
    if (selectedStatus.value === '0') statusParam = 0

    const data = await fetchUsers({
      page: page.value,
      size: size.value,
      keyword: searchKeyword.value.trim(),
      role: selectedRole.value,
      status: statusParam
    })
    users.value = data.records
    total.value = data.total
  } catch {
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  void load()
}

function handleRoleChange(roleKey: string) {
  selectedRole.value = roleKey
  page.value = 1
  void load()
}

function handleStatusChange() {
  page.value = 1
  void load()
}

function openCreate() {
  editing.value = null
  Object.assign(form, { username: '', password: '', nickname: '', role: 'user', status: 1 })
  dialog.value = true
}

function openEdit(row: UserItem) {
  editing.value = row
  Object.assign(form, {
    username: row.username,
    password: '',
    nickname: row.nickname || '',
    role: row.role,
    status: row.status
  })
  dialog.value = true
}

async function submit() {
  try {
    if (editing.value && form.status === 0) {
      const ok = await confirmAction({
        message: `确定要禁用用户「${editing.value.username}」吗？`,
        confirmButtonText: '禁用',
        type: 'warning'
      })
      if (!ok) return
    }

    if (editing.value) {
      await updateUser(editing.value.id, {
        nickname: form.nickname,
        role: form.role,
        status: form.status
      })
      ElMessage.success('更新成功')
    } else {
      if (!form.username || !form.password) {
        ElMessage.warning('请填写用户名和密码')
        return
      }
      await createUser({
        username: form.username,
        password: form.password,
        nickname: form.nickname || form.username,
        role: form.role
      })
      ElMessage.success('创建成功')
    }
    dialog.value = false
    await load()
  } catch {
    ElMessage.error(editing.value ? '更新失败' : '创建失败')
  }
}

async function handleDelete(row: UserItem) {
  try {
    if (!(await confirmDelete(`确定删除用户「${row.username}」？`))) return
    await deleteUser(row.id)
    ElMessage.success('已删除')
    await load()
  } catch {
    ElMessage.error('删除失败')
  }
}

function roleLabel(role: string) {
  return roleOptions.find((r) => r.value === role)?.label || role
}

function getRoleTagType(role: string): '' | 'success' | 'warning' | 'danger' | 'info' {
  if (role === 'super_admin') return 'danger'
  if (role === 'admin') return 'warning'
  return 'info'
}

onMounted(load)
</script>

<template>
  <div class="view-page users-page">
    <PageHeader title="用户管理" subtitle="管理系统账号、角色与启用状态，支持快捷检索与多维筛选。">
      <template #action>
        <el-button @click="openCreate">
          <el-icon class="btn-icon-plus"><Plus /></el-icon>
          新建用户
        </el-button>
      </template>
    </PageHeader>

    <!-- 筛选与搜索工具栏 -->
    <div class="filter-toolbar ao-card">
      <div class="filter-left">
        <!-- 角色筛选卡片 -->
        <div class="filter-tabs">
          <button
            v-for="tab in roleFilterTabs"
            :key="tab.key"
            type="button"
            class="filter-tab-btn"
            :class="{ 'is-active': selectedRole === tab.key }"
            @click="handleRoleChange(tab.key)"
          >
            <span>{{ tab.label }}</span>
          </button>
        </div>

        <!-- 状态筛选 -->
        <div class="status-select-wrap">
          <el-select
            v-model="selectedStatus"
            placeholder="账号状态"
            class="status-select"
            @change="handleStatusChange"
          >
            <el-option
              v-for="opt in statusFilterOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </div>
      </div>

      <div class="filter-search">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索用户名 / 昵称..."
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

    <!-- 用户列表卡片 -->
    <el-card v-loading="loading" shadow="hover" class="content-card">
      <template v-if="users.length">
        <el-table
          :data="users"
          stripe
          border
          highlight-current-row
          header-cell-class-name="table-header-style"
        >
          <el-table-column prop="username" label="用户名" min-width="140" align="center" />
          <el-table-column prop="nickname" label="昵称" min-width="140" align="center">
            <template #default="{ row }">
              <span>{{ row.nickname || '—' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="角色" width="130" align="center">
            <template #default="{ row }">
              <el-tag size="small" effect="plain" :type="getRoleTagType(row.role)" round>
                {{ roleLabel(row.role) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 1 ? 'success' : 'info'" round size="small">
                {{ row.status === 1 ? '正常' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="最近登录" min-width="180" align="center">
            <template #default="{ row }">
              {{ row.lastLoginAt ? new Date(row.lastLoginAt).toLocaleString('zh-CN') : '—' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right" align="center">
            <template #default="{ row }">
              <div class="table-actions">
                <el-button size="small" class="action-btn action-btn--edit" @click="openEdit(row)">编辑</el-button>
                <el-button size="small" class="action-btn action-btn--danger" @click="handleDelete(row)">删除</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <TablePagination v-model:page="page" v-model:size="size" :total="total" @change="load" />
      </template>

      <EmptyState
        v-else
        title="暂无相关用户"
        description="未找到符合搜索条件的用户记录。"
      />
    </el-card>

    <!-- 用户新建/编辑弹窗 -->
    <el-dialog
      v-model="dialog"
      width="480px"
      class="ao-detail-dialog"
      append-to-body
      destroy-on-close
    >
      <template #header>
        <div class="detail-dialog-header">
          <el-icon class="detail-dialog-header__icon"><User /></el-icon>
          <span class="detail-dialog-header__title">{{ editing ? '编辑用户' : '新建用户' }}</span>
        </div>
      </template>

      <el-form label-width="80px" autocomplete="off">
        <!-- 隐式伪装 input 阻止 Chrome/Edge 浏览器自动填充已保存的当前登录账号密码 -->
        <input type="text" style="display: none" />
        <input type="password" style="display: none" />

        <el-form-item v-if="!editing" label="用户名">
          <el-input v-model="form.username" autocomplete="off" placeholder="登录用户名" />
        </el-form-item>

        <el-form-item v-if="!editing" label="密码">
          <el-input v-model="form.password" type="password" autocomplete="new-password" show-password placeholder="至少 6 位" />
        </el-form-item>

        <el-form-item label="昵称">
          <el-input v-model="form.nickname" placeholder="显示名称" />
        </el-form-item>

        <el-form-item label="角色">
          <el-select v-model="form.role" style="width: 100%">
            <el-option
              v-for="opt in roleOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item v-if="editing" label="状态">
          <el-switch
            v-model="form.status"
            :active-value="1"
            :inactive-value="0"
            inline-prompt
            active-text="正常"
            inactive-text="禁用"
            class="status-switch"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="detail-dialog-footer">
          <el-button class="detail-dialog-footer__cancel" @click="dialog = false">取消</el-button>
          <el-button type="primary" class="detail-dialog-footer__submit" @click="submit">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.users-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

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

.filter-left {
  display: flex;
  align-items: center;
  gap: 14px;
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

.status-select-wrap {
  width: 120px;
}

.status-select :deep(.el-input__wrapper) {
  border-radius: 999px !important;
}

.filter-search {
  width: min(240px, 100%);
}

.search-input :deep(.el-input__wrapper) {
  border-radius: 999px !important;
}

.status-switch {
  --el-switch-on-color: #10b981;
  --el-switch-off-color: #94a3b8;
}

.content-card {
  border-radius: 20px;
}

.content-card :deep(.el-card__body) {
  padding: 0 !important;
}
</style>
