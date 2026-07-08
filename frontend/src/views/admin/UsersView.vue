<script setup lang="ts">

import { onMounted, reactive, ref } from 'vue'

import { ElMessage } from 'element-plus'

import { Plus, User } from '@element-plus/icons-vue'

import PageHeader from '@/components/common/PageHeader.vue'
import TablePagination from '@/components/common/TablePagination.vue'
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



onMounted(load)



async function load() {

  loading.value = true

  try {

    const data = await fetchUsers({ page: page.value, size: size.value })

    users.value = data.records

    total.value = data.total

  } catch {

    ElMessage.error('加载用户列表失败')

  } finally {

    loading.value = false

  }

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

</script>



<template>

  <div class="view-page">

    <PageHeader title="用户管理" subtitle="管理系统账号、角色与启用状态。">
      <template #action>
        <el-button @click="openCreate">
          <el-icon class="btn-icon-plus"><Plus /></el-icon>
          新建用户
        </el-button>
      </template>
    </PageHeader>



    <el-card shadow="hover" class="content-card">

      <el-table

        v-loading="loading"

        :data="users"

        stripe

        border

        highlight-current-row

        header-cell-class-name="table-header-style"

      >

        <el-table-column prop="username" label="用户名" min-width="120" align="center" />

        <el-table-column prop="nickname" label="昵称" min-width="120" align="center" />

        <el-table-column label="角色" width="120" align="center">

          <template #default="{ row }">

            <el-tag size="small" effect="plain" round>{{ roleLabel(row.role) }}</el-tag>

          </template>

        </el-table-column>

        <el-table-column label="状态" width="100" align="center">

          <template #default="{ row }">

            <el-tag :type="row.status === 1 ? 'success' : 'info'" round>

              {{ row.status === 1 ? '正常' : '禁用' }}

            </el-tag>

          </template>

        </el-table-column>

        <el-table-column label="最近登录" min-width="160" align="center">

          <template #default="{ row }">

            {{ row.lastLoginAt ? new Date(row.lastLoginAt).toLocaleString('zh-CN') : '—' }}

          </template>

        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right" align="center">

          <template #default="{ row }">

            <div class="table-actions">

              <el-button size="small" class="action-btn action-btn--edit" @click="openEdit(row)">编辑</el-button>

              <el-button size="small" class="action-btn action-btn--danger" @click="handleDelete(row)">删除</el-button>

            </div>

          </template>

        </el-table-column>

      </el-table>

      <TablePagination v-model:page="page" v-model:size="size" :total="total" @change="load" />

    </el-card>



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

      <el-form label-width="80px">

        <el-form-item v-if="!editing" label="用户名">

          <el-input v-model="form.username" placeholder="登录用户名" />

        </el-form-item>

        <el-form-item v-if="!editing" label="密码">

          <el-input v-model="form.password" type="password" show-password placeholder="至少 6 位" />

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
.status-switch {
  --el-switch-on-color: #10b981;
  --el-switch-off-color: #94a3b8;
}
</style>
