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
          <el-option label="自定义（普通 Prompt）" value="custom" />
          <el-option label="Persona · 人设" value="persona" />
          <el-option label="System · 系统" value="system" />
          <el-option label="Planner · 规划" value="planner" />
          <el-option label="Tool · 工具" value="tool" />
          <el-option label="Summary · 总结" value="summary" />
          <el-option label="Prompt Engineer" value="prompt_engineer" />
        </el-select>
        <p class="form-tip">
          「自定义」= 分类标签，表示这是你自己建的 Prompt，不是系统内置那几类；名称和内容在上方自行填写。
          内置类型（Persona 等）请改 <code>backend/app/prompts/*.md</code> 后同步，不要在这里新建同名条目。
        </p>
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

<style scoped>
.form-tip {
  margin: 6px 0 0;
  font-size: 12px;
  line-height: 1.5;
  color: var(--ao-text-muted);
}
</style>
