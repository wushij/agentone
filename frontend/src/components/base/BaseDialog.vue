<template>
  <el-dialog
    v-model="visible"
    :title="title"
    :width="width"
    :destroy-on-close="true"
    @close="$emit('close')"
  >
    <slot />
    <template #footer>
      <slot name="footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="loading" @click="$emit('confirm')">确认</el-button>
      </slot>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    title?: string
    width?: string
    loading?: boolean
  }>(),
  {
    width: '500px',
    loading: false,
  }
)

const emit = defineEmits(['update:modelValue', 'close', 'confirm'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})
</script>
