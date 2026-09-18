import { useAuthStore } from '@/stores/auth'
import { permissionsForRoles, type PermissionCode } from '@/constants/permission'

/** 当前登录角色是否拥有指定权限（任意一个满足即可）。 */
export function hasPermission(...codes: PermissionCode[]): boolean {
  const authStore = useAuthStore()
  const granted = permissionsForRoles(authStore.user?.roleCodes)
  return codes.some((c) => granted.has(c))
}
