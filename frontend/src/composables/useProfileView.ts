import { computed, inject, provide, reactive, ref, watch, type InjectionKey, type Ref } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { changePassword, updateUserProfile } from '@/api/auth'
import { useUserStore } from '@/stores/user'
import type { UserProfile } from '@/types'

export interface ProfileViewContext {
  userStore: ReturnType<typeof useUserStore>
  profile: Ref<UserProfile | null>
  activeTab: Ref<string>
  savingProfile: Ref<boolean>
  savingPassword: Ref<boolean>
  profileFormRef: Ref<FormInstance | undefined>
  passwordFormRef: Ref<FormInstance | undefined>
  fileInputRef: Ref<HTMLInputElement | undefined>
  profileForm: { nickname: string }
  passwordForm: { oldPassword: string; newPassword: string; confirmPassword: string }
  profileRules: FormRules
  passwordRules: FormRules
  roleLabel: Ref<string>
  roleTagType: Ref<'danger' | 'primary' | 'info' | 'success' | 'warning'>
  accountStatusText: Ref<string>
  accountStatusClass: Ref<string>
  triggerUpload: () => void
  onFileChange: (e: Event) => void
  handleUpdateProfile: () => Promise<void>
  handleChangePassword: () => Promise<void>
}

export const PROFILE_VIEW_KEY: InjectionKey<ProfileViewContext> = Symbol('profileView')

export function useProfileViewProvider(): ProfileViewContext {
  const userStore = useUserStore()
  const { profile } = storeToRefs(userStore)

  const activeTab = ref('profile')
  const savingProfile = ref(false)
  const savingPassword = ref(false)
  const profileFormRef = ref<FormInstance>()
  const passwordFormRef = ref<FormInstance>()
  const fileInputRef = ref<HTMLInputElement>()

  const profileForm = reactive({
    nickname: profile.value?.nickname || ''
  })

  const passwordForm = reactive({
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  })

  const profileRules = reactive<FormRules>({
    nickname: [
      { required: true, message: '昵称不能为空', trigger: 'blur' },
      { min: 2, max: 32, message: '昵称长度需在 2 到 32 个字符之间', trigger: 'blur' }
    ]
  })

  const validateConfirmPassword = (_rule: unknown, value: string, callback: (error?: Error) => void) => {
    if (value !== passwordForm.newPassword) {
      callback(new Error('两次输入的密码不一致'))
    } else {
      callback()
    }
  }

  const passwordRules = reactive<FormRules>({
    oldPassword: [{ required: true, message: '原密码不能为空', trigger: 'blur' }],
    newPassword: [
      { required: true, message: '新密码不能为空', trigger: 'blur' },
      { min: 6, max: 32, message: '密码长度需在 6 到 32 个字符之间', trigger: 'blur' }
    ],
    confirmPassword: [
      { required: true, message: '请再次输入新密码确认', trigger: 'blur' },
      { validator: validateConfirmPassword, trigger: 'blur' }
    ]
  })

  const roleLabel = computed(() => {
    const map: Record<string, string> = {
      super_admin: '超级管理员',
      admin: '管理员',
      user: '普通用户'
    }
    return map[userStore.role] || userStore.role
  })

  const roleTagType = computed(() => {
    if (userStore.role === 'super_admin') return 'danger' as const
    if (userStore.role === 'admin') return 'primary' as const
    return 'info' as const
  })

  const accountStatusText = computed(() => {
    if (profile.value?.status === 0) return '已停用'
    return '正常启用'
  })

  const accountStatusClass = computed(() => {
    return profile.value?.status === 0 ? 'status-disabled' : 'status-active'
  })

  watch(
    profile,
    (next) => {
      profileForm.nickname = next?.nickname || next?.username || ''
    },
    { immediate: true }
  )

  function triggerUpload() {
    fileInputRef.value?.click()
  }

  function onFileChange(e: Event) {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (!file) return

    if (file.size > 2 * 1024 * 1024) {
      ElMessage.error('头像图片大小不能超过 2MB')
      return
    }

    if (!file.type.startsWith('image/')) {
      ElMessage.error('只能上传图片文件')
      return
    }

    const reader = new FileReader()
    reader.onload = async (event) => {
      const base64Str = event.target?.result as string
      savingProfile.value = true
      try {
        const updated = await updateUserProfile({
          nickname: profileForm.nickname.trim() || profile.value?.username || '',
          avatar: base64Str
        })
        userStore.updateProfile(updated)
        ElMessage.success('头像上传并保存成功')
      } catch {
        ElMessage.error('头像上传失败，请重试')
      } finally {
        savingProfile.value = false
      }
    }
    reader.readAsDataURL(file)
  }

  async function handleUpdateProfile() {
    if (!profileFormRef.value) return
    await profileFormRef.value.validate(async (valid) => {
      if (!valid) return
      savingProfile.value = true
      try {
        const updated = await updateUserProfile({
          nickname: profileForm.nickname.trim(),
          avatar: profile.value?.avatar
        })
        userStore.updateProfile(updated)
        ElMessage.success('个人基本信息保存成功')
      } catch {
        ElMessage.error('保存失败，请重试')
      } finally {
        savingProfile.value = false
      }
    })
  }

  async function handleChangePassword() {
    if (!passwordFormRef.value) return
    await passwordFormRef.value.validate(async (valid) => {
      if (!valid) return
      savingPassword.value = true
      try {
        await changePassword({
          oldPassword: passwordForm.oldPassword,
          newPassword: passwordForm.newPassword
        })
        ElMessage.success('密码修改成功，请牢记新密码')
        passwordForm.oldPassword = ''
        passwordForm.newPassword = ''
        passwordForm.confirmPassword = ''
        passwordFormRef.value?.resetFields()
      } catch {
        ElMessage.error('原密码校验错误，更新失败')
      } finally {
        savingPassword.value = false
      }
    })
  }

  const ctx: ProfileViewContext = {
    userStore,
    profile,
    activeTab,
    savingProfile,
    savingPassword,
    profileFormRef,
    passwordFormRef,
    fileInputRef,
    profileForm,
    passwordForm,
    profileRules,
    passwordRules,
    roleLabel,
    roleTagType,
    accountStatusText,
    accountStatusClass,
    triggerUpload,
    onFileChange,
    handleUpdateProfile,
    handleChangePassword
  }

  provide(PROFILE_VIEW_KEY, ctx)
  return ctx
}

export function useProfileView(): ProfileViewContext {
  const ctx = inject(PROFILE_VIEW_KEY)
  if (!ctx) {
    throw new Error('useProfileView() must be used within ProfileView')
  }
  return ctx
}
