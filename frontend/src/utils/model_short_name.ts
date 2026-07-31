/**
 * model_short_name.ts — 智能解析模型全名称至简短名称（Short Name）与适用场景描述
 */

export interface ModelMetaInfo {
  shortName: string
  description: string
}

export function parseModelMeta(name: string, modelName = ''): ModelMetaInfo {
  const nameStr = (name || '').toLowerCase()
  const modelNameStr = (modelName || '').toLowerCase()
  const raw = `${nameStr} ${modelNameStr}`

  if (raw.includes('lite') || raw.includes('flash-lite') || raw.includes('mini') || raw.includes('nano')) {
    return {
      shortName: 'Flash-Lite',
      description: '极速回答，轻量低延迟'
    }
  }

  if (raw.includes('coder') || raw.includes('code') || raw.includes('pro') || raw.includes('max')) {
    return {
      shortName: 'Pro',
      description: '高阶数学、复杂代码与架构推演'
    }
  }

  if (raw.includes('deepseek-chat') || raw.includes('deepseek-v3') || nameStr === 'deepseek-chat') {
    return {
      shortName: 'DeepSeek-V3',
      description: '通用对话大模型，全面平衡'
    }
  }

  if (raw.includes('qwen')) {
    return {
      shortName: 'Qwen',
      description: '通义千问大模型服务'
    }
  }

  if (raw.includes('flash')) {
    return {
      shortName: 'Flash',
      description: '全方位帮助，平衡性能与通用能力'
    }
  }

  // 兜底提取短名称
  const cleanName = (name || modelName || 'Model').replace(/^.*[/\\]/, '').trim()
  const parts = cleanName.split(/[-_\s]+/).filter(Boolean)
  const lastPart = parts[parts.length - 1] || 'Model'
  const shortName = lastPart.charAt(0).toUpperCase() + lastPart.slice(1)

  return {
    shortName: shortName.length > 12 ? `${shortName.slice(0, 10)}..` : shortName,
    description: '通用大模型服务'
  }
}
