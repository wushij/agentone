<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import AuthCaptchaField from '@/components/AuthCaptchaField.vue'
import { getCaptcha, getCaptchaRequired, register as registerApi } from '@/api/auth'
import { useUserStore } from '@/stores/user'
import { toCaptchaDataUrl } from '@/utils/captcha'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const username = ref('')
const password = ref('')
const nickname = ref('')
const mode = ref<'login' | 'register'>('login')
const loading = ref(false)
const showPassword = ref(false)
const showCaptcha = ref(false)
const captchaId = ref('')
const captchaImg = ref('')
const captchaAnswer = ref('')

async function refreshCaptcha() {
  const data = await getCaptcha()
  captchaId.value = data.id
  captchaImg.value = toCaptchaDataUrl(data.img)
  captchaAnswer.value = ''
}

async function syncCaptchaState() {
  try {
    const data = await getCaptchaRequired()
    showCaptcha.value = !!data.required
    if (showCaptcha.value) {
      await refreshCaptcha()
    }
  } catch {
    showCaptcha.value = false
  }
}

async function submit() {
  if (loading.value) return

  if (!username.value.trim() || !password.value) {
    ElMessage.warning('请输入账号和密码')
    return
  }

  if (showCaptcha.value && !captchaAnswer.value.trim()) {
    ElMessage.warning('请完成验证码')
    return
  }

  loading.value = true
  try {
    if (mode.value === 'register') {
      const response = await registerApi({
        username: username.value.trim(),
        password: password.value,
        nickname: nickname.value.trim() || username.value.trim(),
        captchaId: showCaptcha.value ? captchaId.value : undefined,
        captchaAnswer: showCaptcha.value ? captchaAnswer.value.trim() : undefined
      })
      userStore.persistSession(response)
      ElMessage.success('注册成功')
    } else {
      await userStore.login({
        username: username.value.trim(),
        password: password.value,
        captchaId: showCaptcha.value ? captchaId.value : undefined,
        captchaAnswer: showCaptcha.value ? captchaAnswer.value.trim() : undefined
      })
      ElMessage.success('登录成功')
    }
    const redirect = route.query.redirect as string | undefined
    await router.replace(redirect && redirect.startsWith('/') ? redirect : '/chat')
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : '登录失败，请检查账号、密码或验证码'
    ElMessage.error(message)
    await syncCaptchaState()
  } finally {
    loading.value = false
  }
}

function fillAccount(role: 'super_admin' | 'admin' | 'user') {
  username.value = role
  password.value = '123456'
}

const isDev = import.meta.env.DEV

onMounted(() => {
  void syncCaptchaState()
})
</script>

<template>
  <section class="auth-panel">
    <div class="auth-welcome">
      <h2>{{ mode === 'login' ? '欢迎登录' : '创建账号' }}</h2>
      <p>{{ mode === 'login' ? '请使用您的 AgentOne 账号进入系统' : '注册后即可使用 AI 对话与管理功能' }}</p>
    </div>

    <div class="auth-mode-tabs">
      <button type="button" :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
      <button type="button" :class="{ active: mode === 'register' }" @click="mode = 'register'">注册</button>
    </div>

    <el-form class="auth-form" @submit.prevent="submit">
      <el-form-item>
        <el-input v-model="username" placeholder="用户名" autocomplete="username" size="large" :prefix-icon="User" />
      </el-form-item>

      <el-form-item v-if="mode === 'register'">
        <el-input v-model="nickname" placeholder="昵称（可选）" size="large" />
      </el-form-item>

      <el-form-item>
        <el-input
          v-model="password"
          :type="showPassword ? 'text' : 'password'"
          placeholder="密码"
          autocomplete="current-password"
          size="large"
          :prefix-icon="Lock"
          @keyup.enter="submit"
        >
          <template #suffix>
            <button
              type="button"
              class="auth-eye-btn"
              tabindex="-1"
              :aria-label="showPassword ? '隐藏密码' : '显示密码'"
              @click="showPassword = !showPassword"
            >
              <svg
                v-if="showPassword"
                viewBox="0 0 24 24"
                width="15"
                height="15"
                fill="none"
                stroke="currentColor"
                stroke-width="1.75"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                <circle cx="12" cy="12" r="3" />
              </svg>
              <svg
                v-else
                viewBox="0 0 24 24"
                width="15"
                height="15"
                fill="none"
                stroke="currentColor"
                stroke-width="1.75"
                stroke-linecap="round"
                stroke-linejoin="round"
                aria-hidden="true"
              >
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                <circle cx="12" cy="12" r="3" />
                <line x1="3" y1="4" x2="21" y2="20" />
              </svg>
            </button>
          </template>
        </el-input>
      </el-form-item>

      <el-form-item v-show="showCaptcha">
        <AuthCaptchaField
          v-model="captchaAnswer"
          :captcha-img="captchaImg"
          @refresh="refreshCaptcha"
          @enter="submit"
        />
      </el-form-item>

      <el-button type="primary" class="auth-submit" size="large" :loading="loading" native-type="submit">
        {{ mode === 'login' ? '登 录' : '注 册' }}
      </el-button>
    </el-form>

    <div v-if="isDev" class="auth-demo">
      <span class="auth-demo__label">演示账号</span>
      <div class="auth-demo__accounts">
        <div class="accounts-row">
          <el-button text @click="fillAccount('super_admin')">super_admin</el-button>
          <el-button text @click="fillAccount('admin')">admin</el-button>
          <el-button text @click="fillAccount('user')">user</el-button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.auth-panel {
  background: rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 80px 40px 36px;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  height: 100%;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
}

.auth-welcome {
  text-align: center;
  margin-bottom: 24px;
  flex-shrink: 0;
}

.auth-welcome h2 {
  margin: 0;
  font-size: 30px;
  font-weight: 800;
  letter-spacing: -0.5px;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #2563eb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.auth-welcome p {
  margin: 8px 0 0;
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
  letter-spacing: 0.5px;
}

.auth-mode-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  width: 100%;
}

.auth-mode-tabs button {
  flex: 1;
  height: 40px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.6);
  font-weight: 700;
  color: #64748b;
  cursor: pointer;
}

.auth-mode-tabs button.active {
  color: #fff;
  border-color: transparent;
  background: linear-gradient(135deg, #4f46e5, #8b5cf6);
}

.auth-form {
  flex-shrink: 0;
  min-height: auto;
}

.auth-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.auth-form :deep(.el-input__wrapper) {
  height: 50px;
  border-radius: 9999px !important;
  background: rgba(255, 255, 255, 0.45) !important;
  box-shadow: 0 0 0 1px rgba(148, 163, 184, 0.15) inset !important;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
  backdrop-filter: blur(4px);
}

.auth-form :deep(.el-input__wrapper:hover) {
  background: rgba(255, 255, 255, 0.7) !important;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.25) inset !important;
}

.auth-form :deep(.el-input__wrapper.is-focus) {
  background: #ffffff !important;
  transform: translateY(-1px);
  box-shadow:
    0 0 0 1px #3b82f6 inset,
    0 4px 16px rgba(59, 130, 246, 0.12) !important;
}

.auth-form :deep(.el-input__inner) {
  color: #1a1d26;
  font-weight: 500;
  text-align: left;
}

.auth-form :deep(.el-input__prefix .el-icon) {
  color: #94a3b8;
  font-size: 15px;
}

.auth-submit {
  width: 100%;
  height: 50px !important;
  margin-top: 6px;
  font-size: 15px !important;
  font-weight: 700 !important;
  letter-spacing: 4px;
  border-radius: 9999px !important;
  border: none !important;
  background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 50%, #8b5cf6 100%) !important;
  background-size: 200% auto !important;
  color: #ffffff !important;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.25) !important;
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.auth-panel :deep(.auth-submit.el-button--primary:hover),
.auth-panel :deep(.auth-submit.el-button--primary:focus) {
  transform: translateY(-2px) !important;
  background-position: right center !important;
  box-shadow:
    0 8px 24px rgba(99, 102, 241, 0.45),
    0 0 0 1px rgba(255, 255, 255, 0.1) inset !important;
}

.auth-eye-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  margin-right: -2px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  padding: 0;
  transition: color 0.15s ease, background-color 0.15s ease;
}

.auth-eye-btn:hover {
  color: #4b5563;
  background: rgba(148, 163, 184, 0.12);
}

.auth-demo {
  margin-top: 24px;
  padding-top: 18px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  color: #64748b;
  font-size: 13px;
  border-top: 1px solid rgba(148, 163, 184, 0.14);
}

.auth-demo__label {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.5px;
  color: #94a3b8;
  margin-top: 8px;
}

.auth-demo__accounts {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.accounts-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.auth-demo__accounts :deep(.el-button) {
  flex-shrink: 0;
  margin: 0;
  padding: 6px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(148, 163, 184, 0.16);
  color: #475569;
  transition: all 0.2s ease;
}

.auth-demo__accounts :deep(.el-button:hover) {
  color: #2563eb;
  border-color: rgba(59, 130, 246, 0.28);
  background: rgba(255, 255, 255, 0.9);
}

@media (max-width: 840px) {
  .auth-panel {
    padding: 36px 28px 28px;
    background: rgba(255, 255, 255, 0.88);
  }

  .auth-demo {
    align-items: flex-start;
    flex-direction: column;
  }

  .auth-demo__accounts {
    width: 100%;
  }
}
</style>
