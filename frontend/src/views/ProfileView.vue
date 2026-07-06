<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Camera, User, Lock, Calendar, CircleCheck } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { changePassword, updateUserProfile } from '@/api/auth'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const { profile } = storeToRefs(userStore)

const activeTab = ref('profile')
const savingProfile = ref(false)
const savingPassword = ref(false)

const profileFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()
const fileInputRef = ref<HTMLInputElement>()

const profileForm = reactive({
  nickname: profile.value?.nickname || ''
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const profileRules = reactive<FormRules>({
  nickname: [
    { required: true, message: '昵称不能为空', trigger: 'blur' },
    { min: 2, max: 32, message: '昵称长度需在 2 到 32 个字符之间', trigger: 'blur' }
  ]
})

const validateConfirmPassword = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = reactive<FormRules>({
  oldPassword: [{ required: true, message: '原密码不能为空', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '新密码不能为空', trigger: 'blur' },
    { min: 6, max: 32, message: '密码长度需在 6 到 32 个字符之间', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码确认', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
})

const roleLabel = computed(() => {
  const map: Record<string, string> = {
    super_admin: '超级管理员',
    admin: '管理员',
    user: '普通用户'
  }
  return map[userStore.role] || userStore.role
})

const roleTagType = computed(() => {
  if (userStore.role === 'super_admin') return 'danger'
  if (userStore.role === 'admin') return 'primary'
  return 'info'
})

const accountStatusText = computed(() => {
  if (profile.value?.status === 0) return '已停用'
  return '正常启用'
})

const accountStatusClass = computed(() => {
  return profile.value?.status === 0 ? 'status-disabled' : 'status-active'
})

watch(
  profile,
  (next) => {
    profileForm.nickname = next?.nickname || next?.username || ''
  },
  { immediate: true }
)

function triggerUpload() {
  fileInputRef.value?.click()
}

function onFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return

  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('头像图片大小不能超过 2MB')
    return
  }

  if (!file.type.startsWith('image/')) {
    ElMessage.error('只能上传图片文件')
    return
  }

  const reader = new FileReader()
  reader.onload = async (event) => {
    const base64Str = event.target?.result as string
    savingProfile.value = true
    try {
      const updated = await updateUserProfile({
        nickname: profileForm.nickname.trim() || profile.value?.username || '',
        avatar: base64Str
      })
      userStore.updateProfile(updated)
      ElMessage.success('头像上传并保存成功')
    } catch {
      ElMessage.error('头像上传失败，请重试')
    } finally {
      savingProfile.value = false
    }
  }
  reader.readAsDataURL(file)
}

async function handleUpdateProfile() {
  if (!profileFormRef.value) return
  await profileFormRef.value.validate(async (valid) => {
    if (!valid) return
    savingProfile.value = true
    try {
      const updated = await updateUserProfile({
        nickname: profileForm.nickname.trim(),
        avatar: profile.value?.avatar
      })
      userStore.updateProfile(updated)
      ElMessage.success('个人基本信息保存成功')
    } catch {
      ElMessage.error('保存失败，请重试')
    } finally {
      savingProfile.value = false
    }
  })
}

async function handleChangePassword() {
  if (!passwordFormRef.value) return
  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    savingPassword.value = true
    try {
      await changePassword({
        oldPassword: passwordForm.oldPassword,
        newPassword: passwordForm.newPassword
      })
      ElMessage.success('密码修改成功，请牢记新密码')
      passwordForm.oldPassword = ''
      passwordForm.newPassword = ''
      passwordForm.confirmPassword = ''
      passwordFormRef.value?.resetFields()
    } catch {
      ElMessage.error('原密码校验错误，更新失败')
    } finally {
      savingPassword.value = false
    }
  })
}
</script>

<template>
  <div class="view-page profile-page">
    <PageHeader title="个人中心" subtitle="管理您的个人头像、基本账户信息与账户安全设置" />

    <el-row :gutter="16" class="profile-layout">
      <el-col :xs="24" :md="8" class="layout-col">
        <el-card shadow="hover" class="user-profile-card">
          <div class="avatar-container">
            <div class="avatar-wrapper" title="点击上传新头像" @click="triggerUpload">
              <el-avatar :size="100" :src="profile?.avatar" class="user-avatar-img">
                <span v-if="!profile?.avatar" class="avatar-initial">
                  {{ userStore.displayName.slice(0, 1) }}
                </span>
              </el-avatar>
              <div class="avatar-hover-mask">
                <el-icon class="upload-icon"><Camera /></el-icon>
                <span>更换头像</span>
              </div>
            </div>
            <input
              ref="fileInputRef"
              type="file"
              style="display: none"
              accept="image/*"
              @change="onFileChange"
            />
            <el-tag round :type="roleTagType" effect="dark" class="role-tag">
              {{ roleLabel }}
            </el-tag>
          </div>

          <div class="user-details">
            <h2 class="user-realname">{{ userStore.displayName }}</h2>
            <p class="user-username">@{{ profile?.username || 'user' }}</p>
          </div>

          <div class="meta-list">
            <div class="meta-item">
              <div class="meta-left">
                <el-icon class="meta-icon"><User /></el-icon>
                <span class="meta-label">账号角色</span>
              </div>
              <span class="meta-value">{{ roleLabel }}</span>
            </div>

            <div class="meta-item">
              <div class="meta-left">
                <el-icon class="meta-icon"><Calendar /></el-icon>
                <span class="meta-label">用户 ID</span>
              </div>
              <span class="meta-value">{{ profile?.id ?? '—' }}</span>
            </div>

            <div class="meta-item">
              <div class="meta-left">
                <el-icon class="meta-icon"><CircleCheck /></el-icon>
                <span class="meta-label">账户状态</span>
              </div>
              <span class="meta-value" :class="accountStatusClass">{{ accountStatusText }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="16" class="layout-col">
        <el-card shadow="hover" class="settings-card">
          <el-tabs v-model="activeTab" class="settings-tabs">
            <el-tab-pane name="profile">
              <template #label>
                <span class="tab-label">
                  <el-icon><User /></el-icon>
                  <span>基本资料</span>
                </span>
              </template>

              <el-form
                ref="profileFormRef"
                :model="profileForm"
                :rules="profileRules"
                label-position="top"
                class="settings-form"
              >
                <el-form-item label="登录账号（无法修改）">
                  <el-input :model-value="profile?.username" disabled class="capsule-input" />
                </el-form-item>

                <el-form-item label="昵称" prop="nickname">
                  <el-input
                    v-model="profileForm.nickname"
                    placeholder="请输入您的昵称"
                    class="capsule-input"
                    maxlength="32"
                  />
                </el-form-item>

                <div class="form-actions">
                  <el-button
                    type="primary"
                    :loading="savingProfile"
                    class="pill-btn"
                    @click="handleUpdateProfile"
                  >
                    保存修改
                  </el-button>
                </div>
              </el-form>
            </el-tab-pane>

            <el-tab-pane name="password">
              <template #label>
                <span class="tab-label">
                  <el-icon><Lock /></el-icon>
                  <span>修改密码</span>
                </span>
              </template>

              <el-form
                ref="passwordFormRef"
                :model="passwordForm"
                :rules="passwordRules"
                label-position="top"
                class="settings-form"
              >
                <el-form-item label="当前原密码" prop="oldPassword">
                  <el-input
                    v-model="passwordForm.oldPassword"
                    type="password"
                    show-password
                    placeholder="请输入当前的原密码"
                    class="capsule-input"
                  />
                </el-form-item>

                <el-form-item label="新密码" prop="newPassword">
                  <el-input
                    v-model="passwordForm.newPassword"
                    type="password"
                    show-password
                    placeholder="建议包含字母、数字及符号，6-32 位"
                    class="capsule-input"
                  />
                </el-form-item>

                <el-form-item label="确认新密码" prop="confirmPassword">
                  <el-input
                    v-model="passwordForm.confirmPassword"
                    type="password"
                    show-password
                    placeholder="请再次输入新密码"
                    class="capsule-input"
                  />
                </el-form-item>

                <div class="form-actions">
                  <el-button
                    type="primary"
                    :loading="savingPassword"
                    class="pill-btn"
                    @click="handleChangePassword"
                  >
                    更新密码
                  </el-button>
                </div>
              </el-form>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.profile-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.profile-layout {
  display: flex;
  align-items: stretch;
  margin-top: 4px;
}

.layout-col {
  display: flex;
  flex-direction: column;
}

.user-profile-card {
  border-radius: 16px;
  padding: 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.user-profile-card .el-card__body) {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  height: 100%;
}

.avatar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  margin-top: 8px;
  margin-bottom: 16px;
}

.avatar-wrapper {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(79, 70, 229, 0.15);
  cursor: pointer;
  background: var(--theme-primary-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-avatar-img {
  background: transparent;
  transition: all 0.3s ease;
}

.avatar-hover-mask {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.72);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.avatar-wrapper:hover .avatar-hover-mask {
  opacity: 1;
}

.avatar-wrapper:hover .user-avatar-img {
  transform: scale(1.06);
}

.upload-icon {
  font-size: 18px;
}

.avatar-initial {
  color: #fff;
  font-size: 42px;
  font-weight: 700;
}

.role-tag {
  font-weight: 600;
  font-size: 12px;
  padding: 2px 12px;
}

.user-details {
  margin-bottom: 24px;
  text-align: center;
}

.user-realname {
  font-size: 20px;
  font-weight: 700;
  color: var(--ao-text-primary);
  margin: 0 0 4px;
}

.user-username {
  font-size: 13px;
  color: var(--ao-text-secondary);
  margin: 0;
}

.meta-list {
  border-top: 1px solid var(--ao-border);
  padding-top: 20px;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.meta-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: var(--ao-surface-muted);
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 13px;
  transition: background-color 0.2s ease;
}

.meta-item:hover {
  background-color: var(--ao-surface);
}

.meta-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-icon {
  font-size: 16px;
  color: var(--ao-text-secondary);
}

.meta-label {
  color: var(--ao-text-secondary);
  font-weight: 500;
}

.meta-value {
  color: var(--ao-text-primary);
  font-weight: 600;
}

.status-active {
  color: #10b981;
}

.status-disabled {
  color: #e11d48;
}

.settings-card {
  border-radius: 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.settings-card .el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 24px;
}

.settings-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.settings-tabs :deep(.el-tabs__content) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding-top: 8px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 6px;
}

.settings-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
}

.settings-tabs :deep(.el-tabs__item) {
  font-size: 14px;
  font-weight: 600;
  color: var(--ao-text-secondary);
}

.settings-tabs :deep(.el-tabs__item.is-active) {
  color: var(--theme-primary);
}

.settings-tabs :deep(.el-tabs__active-bar) {
  background-color: var(--theme-primary);
  height: 3px;
  border-radius: 3px;
}

.settings-form {
  max-width: 480px;
  width: 100%;
}

.settings-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.settings-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: var(--ao-text-secondary);
  font-size: 13px;
  margin-bottom: 6px;
  padding: 0;
}

.capsule-input :deep(.el-input__wrapper) {
  border-radius: 20px;
  padding-left: 16px;
  padding-right: 16px;
  height: 42px;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
  transition: all 0.3s ease;
}

.capsule-input :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    0 0 0 1px var(--theme-primary) inset,
    0 0 0 3px var(--theme-primary-muted) !important;
}

.pill-btn {
  border-radius: 20px;
  padding: 10px 24px;
  font-weight: 600;
  font-size: 13px;
  height: 40px;
}

.form-actions {
  margin-top: 24px;
}
</style>
