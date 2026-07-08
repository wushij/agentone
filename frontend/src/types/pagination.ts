export interface ApiPage<T> {
  records: T[]
  total: number
}

export interface ApiListParams {
  page?: number
  size?: number
  keyword?: string
  q?: string
}
