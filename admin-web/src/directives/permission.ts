import type { App, DirectiveBinding } from 'vue'
import { hasPermission } from '@/utils/permission'
import type { PermissionCode } from '@/constants/permission'

/**
 * v-permission="'APPEAL_HANDLE'" 或 v-permission="['APPEAL_HANDLE','APPEAL_DEPT_REPLY']"
 *
 * 当前角色不具备（任一）所需权限时，直接从 DOM 中移除该元素——
 * 这只是用户体验层面的隐藏，真正的访问控制在后端（require_permissions）。
 */
function check(el: HTMLElement, binding: DirectiveBinding<PermissionCode | PermissionCode[]>) {
  const codes = Array.isArray(binding.value) ? binding.value : [binding.value]
  if (!hasPermission(...codes)) {
    el.remove()
  }
}

export function installPermissionDirective(app: App) {
  app.directive('permission', {
    mounted: check,
  })
}
