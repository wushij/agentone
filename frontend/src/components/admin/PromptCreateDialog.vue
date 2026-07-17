<script setup lang="ts">
import { Plus } from '@element-plus/icons-vue'
import { usePromptsAdmin } from '@/composables/usePromptsAdmin'

const { createOpen, newPrompt, create } = usePromptsAdmin()
</script>

<template>
  <el-dialog
    v-model="createOpen"
    width="560px"
    class="ao-detail-dialog"
    append-to-body
    destroy-on-close
  >
    <template #header>
      <div class="detail-dialog-header">
        <el-icon class="detail-dialog-header__icon"><Plus /></el-icon>
        <span class="detail-dialog-header__title">新建 Prompt</span>
      </div>
    </template>

    <el-form label-width="80px">
      <el-form-item label="名称">
        <el-input v-model="newPrompt.name" placeholder="例如 custom_assistant" />
      </el-form-item>
      <el-form-item label="类型">
        <el-select v-model="newPrompt.type" style="width: 100%">
          <el-option label="自定义" value="custom" />
          <el-option label="Persona" value="persona" />
          <el-option label="System" value="system" />
          <el-option label="Planner" value="planner" />
          <el-option label="Tool" value="tool" />
          <el-option label="Summary" value="summary" />
          <el-option label="Prompt Engineer" value="prompt_engineer" />
        </el-select>
      </el-form-item>
      <el-form-item label="内容">
        <el-input v-model="newPrompt.content" type="textarea" :rows="10" />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="detail-dialog-footer">
        <el-button class="detail-dialog-footer__cancel" @click="createOpen = false">取消</el-button>
        <el-button type="primary" class="detail-dialog-footer__submit" @click="create">创建</el-button>
      </div>
    </template>
  </el-dialog>
</template>
