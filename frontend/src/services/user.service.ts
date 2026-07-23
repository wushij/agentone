/**
 * src/services/user.service.ts — 用户鉴权与个人中心服务层
 */

import { login, register, getCaptcha } from '@/api/auth'
import type { LoginPayload } from '@/types'

export class UserService {
  static async login(data: LoginPayload) {
    return login(data)
  }

  static async register(data: { username: string; password: string; nickname?: string }) {
    return register(data)
  }

  static async getCaptcha() {
    return getCaptcha()
  }
}
