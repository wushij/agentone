/**
 * Permission matching with wildcard support.
 * `*` grants full access; `chat:*` matches `chat:read`, etc.
 */
export function matchPermission(
  userPermissions: string[],
  required?: string | string[],
  fullAccess = false
): boolean {
  if (fullAccess) return true
  if (!required) return true

  const requiredList = Array.isArray(required) ? required : [required]
  if (requiredList.length === 0) return true
  if (userPermissions.includes('*')) return true

  return requiredList.every((req) => {
    if (userPermissions.includes(req)) return true

    const [prefix, action] = req.split(':')
    if (userPermissions.includes(`${prefix}:*`)) return true

    return userPermissions.some((perm) => {
      if (perm === '*') return true
      if (!perm.includes('*')) return false
      const pattern = perm.replace(/[.+?^${}()|[\]\\]/g, '\\$&').replace(/\*/g, '.*')
      return new RegExp(`^${pattern}$`).test(req) || (action && new RegExp(`^${pattern}$`).test(`${prefix}:*`))
    })
  })
}
