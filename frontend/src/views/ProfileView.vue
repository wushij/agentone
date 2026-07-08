<script setup lang="ts">
import PageHeader from '@/components/common/PageHeader.vue'
import ProfileSidebarCard from '@/components/profile/ProfileSidebarCard.vue'
import ProfileSettingsCard from '@/components/profile/ProfileSettingsCard.vue'
import { useProfileViewProvider } from '@/composables/useProfileView'

useProfileViewProvider()
</script>

<template>
  <div class="view-page profile-page">
    <PageHeader title="个人中心" subtitle="管理您的个人头像、基本账户信息与账户安全设置" />

    <el-row :gutter="16" class="profile-layout">
      <ProfileSidebarCard />
      <ProfileSettingsCard />
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
</style>
