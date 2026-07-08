<script setup lang="ts">
import { User, Lock } from '@element-plus/icons-vue'
import { useProfileView } from '@/composables/useProfileView'

const {
  profile,
  activeTab,
  savingProfile,
  savingPassword,
  profileFormRef,
  passwordFormRef,
  profileForm,
  passwordForm,
  profileRules,
  passwordRules,
  handleUpdateProfile,
  handleChangePassword
} = useProfileView()
</script>

<template>
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
</template>

<style scoped>
.layout-col {
  display: flex;
  flex-direction: column;
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
