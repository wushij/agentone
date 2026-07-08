/** Prompt 类型枚举 → 界面展示文案 */
export const PROMPT_TYPE_LABELS: Record<string, string> = {
  custom: '自定义',
  persona: 'Persona',
  system: 'System',
  planner: 'Planner',
  tool: 'Tool',
  summary: 'Summary',
  prompt_engineer: 'Prompt Engineer'
}

export function promptTypeLabel(type?: string) {
  if (!type) return '—'
  return PROMPT_TYPE_LABELS[type] ?? type
}

/** 系统内置 Prompt，不可删除（可停用或改文件同步） */
export const BUILTIN_PROMPT_NAMES = new Set([
  'persona',
  'system',
  'planner',
  'tool',
  'summary',
  'prompt_engineer'
])

export function canDeletePrompt(row: { name: string; type?: string }) {
  return row.type === 'custom' && !BUILTIN_PROMPT_NAMES.has(row.name)
}
