import type { ApiPage } from '@/types/pagination'

export function normalizePage<T>(data: ApiPage<T> | T[] | null | undefined): ApiPage<T> {
  if (!data) return { records: [], total: 0 }
  if (Array.isArray(data)) return { records: data, total: data.length }
  return {
    records: data.records ?? [],
    total: Number(data.total ?? 0)
  }
}

const PICKER_PAGE_SIZE = 100

/** 下拉/选择器：按页拉取直至拿全量（单页最大 100） */
export async function fetchAllPages<T>(
  fetcher: (page: number, size: number) => Promise<ApiPage<T>>,
  pageSize = PICKER_PAGE_SIZE
): Promise<T[]> {
  const first = await fetcher(1, pageSize)
  const records = [...first.records]
  const totalPages = Math.ceil(first.total / pageSize)
  for (let page = 2; page <= totalPages; page++) {
    const next = await fetcher(page, pageSize)
    records.push(...next.records)
  }
  return records
}
