/**
 * 前端权限常量与角色-权限映射。
 *
 * 必须与后端 app/constants/permission.py 保持一致——但请注意：这里只影响 UI 体验
 * （菜单/按钮是否显示），真正的访问控制边界在后端（见 app/core/permission.py 的
 * require_permissions），前端权限缺失或被绕过都不能让用户实际越权操作到数据。
 */

export const Permission = {
  APPEAL_VIEW: 'APPEAL_VIEW',
  APPEAL_HANDLE: 'APPEAL_HANDLE',
  APPEAL_DEPT_REPLY: 'APPEAL_DEPT_REPLY',
  MEETING_ROOM_VIEW: 'MEETING_ROOM_VIEW',
  MEETING_ROOM_MANAGE: 'MEETING_ROOM_MANAGE',
  MEETING_BOOKING_HANDLE: 'MEETING_BOOKING_HANDLE',
  GOV_MEETING_VIEW: 'GOV_MEETING_VIEW',
  GOV_MEETING_HANDLE: 'GOV_MEETING_HANDLE',
  DICT_MANAGE: 'DICT_MANAGE',
  OPERATION_LOG_VIEW: 'OPERATION_LOG_VIEW',
  DASHBOARD_VIEW: 'DASHBOARD_VIEW',
} as const

export type PermissionCode = (typeof Permission)[keyof typeof Permission]

const ALL_PERMISSIONS = Object.values(Permission)

export const ROLE_PERMISSIONS: Record<string, PermissionCode[]> = {
  PLATFORM_ADMIN: [...ALL_PERMISSIONS],
  CITY_ADMIN: [...ALL_PERMISSIONS],
  CENTER_ADMIN: [
    Permission.APPEAL_VIEW,
    Permission.APPEAL_HANDLE,
    Permission.MEETING_ROOM_VIEW,
    Permission.MEETING_ROOM_MANAGE,
    Permission.MEETING_BOOKING_HANDLE,
    Permission.GOV_MEETING_VIEW,
    Permission.GOV_MEETING_HANDLE,
    Permission.DICT_MANAGE,
    Permission.OPERATION_LOG_VIEW,
    Permission.DASHBOARD_VIEW,
  ],
  CENTER_STAFF: [
    Permission.APPEAL_VIEW,
    Permission.APPEAL_HANDLE,
    Permission.MEETING_ROOM_VIEW,
    Permission.MEETING_BOOKING_HANDLE,
    Permission.GOV_MEETING_VIEW,
    Permission.GOV_MEETING_HANDLE,
    Permission.DASHBOARD_VIEW,
  ],
  DEPT_USER: [Permission.APPEAL_VIEW, Permission.APPEAL_DEPT_REPLY],
  ROOM_ADMIN: [
    Permission.MEETING_ROOM_VIEW,
    Permission.MEETING_ROOM_MANAGE,
    Permission.MEETING_BOOKING_HANDLE,
  ],
}

export function permissionsForRoles(roleCodes: string[] | undefined | null): Set<PermissionCode> {
  const result = new Set<PermissionCode>()
  for (const role of roleCodes || []) {
    for (const p of ROLE_PERMISSIONS[role] || []) result.add(p)
  }
  return result
}
