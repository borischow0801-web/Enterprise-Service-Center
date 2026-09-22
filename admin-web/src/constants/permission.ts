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
  ADMIN_USER_MANAGE: 'ADMIN_USER_MANAGE',
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

/** 角色编码取自 第一阶段数据库与后端接口设计说明.md §13.2，与后端
 * app/constants/permission.py::AdminRole 保持一致。登录页（开发调试登录）和
 * 管理员管理页共用同一份，避免角色文案在两处漂移。 */
export const ADMIN_ROLE_OPTIONS: { label: string; value: string }[] = [
  { label: '平台管理员 (PLATFORM_ADMIN)', value: 'PLATFORM_ADMIN' },
  { label: '市级管理员 (CITY_ADMIN)', value: 'CITY_ADMIN' },
  { label: '企服中心管理员 (CENTER_ADMIN)', value: 'CENTER_ADMIN' },
  { label: '企服中心工作人员 (CENTER_STAFF)', value: 'CENTER_STAFF' },
  { label: '部门办理人员 (DEPT_USER)', value: 'DEPT_USER' },
  { label: '会议室管理员 (ROOM_ADMIN)', value: 'ROOM_ADMIN' },
]
