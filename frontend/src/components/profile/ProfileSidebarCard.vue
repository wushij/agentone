<script setup lang="ts">
import { Camera, User, Calendar, CircleCheck } from '@element-plus/icons-vue'
import { useProfileView } from '@/composables/useProfileView'

const {
  userStore,
  profile,
  roleLabel,
  roleTagType,
  accountStatusText,
  accountStatusClass,
  fileInputRef,
  triggerUpload,
  onFileChange
} = useProfileView()
</script>

<template>
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
</template>

<style scoped>
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
</style>
