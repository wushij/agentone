/** Parse API datetime strings; naive values are treated as UTC. */
export function parseApiDate(value: string): Date {
  if (!value) return new Date(Number.NaN)
  const normalized = /(?:Z|[+-]\d{2}:\d{2})$/.test(value) ? value : `${value}Z`
  return new Date(normalized)
}

export function formatDateTime(value: string, withSeconds = true): string {
  const date = parseApiDate(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', {
    hour12: false,
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    ...(withSeconds ? { second: '2-digit' } : {})
  })
}
