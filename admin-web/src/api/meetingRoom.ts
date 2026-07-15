import { get, post, put, patch, del } from './request'
import type { PageResult } from './appeal'

// ── Interfaces ────────────────────────────────────────────────────────────────

export interface MeetingRoom {
  id: number
  roomName: string
  roomType?: string
  roomTypeName?: string
  regionCode: string
  regionName: string
  serviceCenterId?: number | null
  serviceCenterName?: string | null
  address?: string
  capacity: number
  facilities: string[]
  description?: string
  coverAttachmentId?: number
  coverImageUrl?: string
  images?: RoomImageItem[]
  bookingNotice?: string
  status: string
  createdAt?: string
}

export interface RoomImageItem {
  attachmentId: number
  url: string
  isCover: number
  sortNo: number
}

export interface ServiceCenter {
  id: number
  centerName: string
  regionCode: string
  regionName: string
  address?: string
  contactName?: string
  contactPhone?: string
  status: string
}

export interface OpenRuleItem {
  weekday: number   // 1=Mon...7=Sun
  openFlag: number  // 1=open 0=closed
  startTime?: string // "HH:MM"
  endTime?: string
}

export interface MaterialRule {
  id: number
  roomId?: number
  regionCode?: string
  regionName?: string
  serviceCenterId?: number
  serviceCenterName?: string
  enterpriseType?: string
  materialName: string
  materialCode: string
  requiredFlag: number
  templateAttachmentId?: number
  description?: string
  sortNo?: number
  enabled: number
}

export interface BookingAttachment {
  id: number
  originalName: string
  fileExt?: string
  fileSize?: number
  fileCategory?: string
  createdAt?: string
  downloadUrl?: string
}

export interface BookingMaterialGroup {
  materialCode: string
  materialName: string
  requiredFlag?: number
  description?: string
  attachments?: BookingAttachment[]
}

export interface BookingRoomInfo {
  roomName?: string
  address?: string
  capacity?: number
  facilities?: string[]
  serviceCenterName?: string
}

export interface BookingEnterpriseInfo {
  id?: number
  enterpriseName?: string
  creditCode?: string
  regionName?: string
  meetingNoShowCount?: number
  meetingBookingDisabled?: boolean
}

export interface BookingUsageRecord {
  id?: number
  usageStatus?: string
  actualStartTime?: string
  actualEndTime?: string
  confirmUserName?: string
  confirmTime?: string
  remark?: string
}

export interface MeetingBooking {
  id: number
  bookingNo: string
  roomId: number
  roomName: string
  enterpriseId?: number
  enterpriseName: string
  creditCode: string
  regionCode?: string
  regionName?: string
  serviceCenterId?: number
  meetingSubject: string
  participantCount: number
  contactName: string
  contactPhone: string
  startTime?: string
  endTime?: string
  supportItems?: string[]
  status: string
  cancelReason?: string
  canceledAt?: string
  submittedAt?: string
  approvedAt?: string
  completedAt?: string
  createdAt?: string
  enterpriseType?: string
  enterpriseTypeName?: string
  attachments?: BookingAttachment[]
  materials?: BookingMaterialGroup[]
  auditRecords?: BookingAuditRecord[]
  usageRecord?: BookingUsageRecord | null
  roomInfo?: BookingRoomInfo
  enterpriseInfo?: BookingEnterpriseInfo
}

export interface BookingAuditRecord {
  id: number
  actionType?: string
  action?: string
  actionName?: string
  beforeStatus?: string
  afterStatus?: string
  auditOpinion?: string
  opinion?: string
  operatorName?: string
  operatorDeptName?: string
  createdAt: string
}

export interface MeetingRoomListParams {
  regionCode?: string
  serviceCenterId?: number
  status?: string
  roomType?: string
  capacityMin?: number
  pageNo?: number
  pageSize?: number
}

export interface BookingListParams {
  roomId?: number
  enterpriseName?: string
  creditCode?: string
  status?: string
  startDate?: string
  endDate?: string
  regionCode?: string
  serviceCenterId?: number
  pageNo?: number
  pageSize?: number
}

// ── Meeting Room CRUD ─────────────────────────────────────────────────────────

export function getMeetingRoomList(params: MeetingRoomListParams): Promise<PageResult<MeetingRoom>> {
  return get<PageResult<MeetingRoom>>('/api/admin/meeting-rooms', params as Record<string, unknown>)
}

export function getMeetingRoomDetail(id: number): Promise<MeetingRoom> {
  return get<MeetingRoom>(`/api/admin/meeting-rooms/${id}`)
}

export function getServiceCenterList(params?: { regionCode?: string }): Promise<ServiceCenter[]> {
  return get<ServiceCenter[]>('/api/admin/service-centers', params as Record<string, unknown>)
}

export function createMeetingRoom(data: {
  roomName: string
  roomType?: string
  regionCode: string
  regionName: string
  serviceCenterId?: number | null
  serviceCenterName?: string | null
  address?: string
  capacity: number
  facilities?: string[]
  description?: string
  coverAttachmentId?: number
  bookingNotice?: string
}): Promise<MeetingRoom> {
  return post<MeetingRoom>('/api/admin/meeting-rooms', data)
}

export function updateMeetingRoom(id: number, data: {
  roomName?: string
  roomType?: string
  regionCode?: string
  regionName?: string
  serviceCenterId?: number | null
  serviceCenterName?: string | null
  address?: string
  capacity?: number
  facilities?: string[]
  description?: string
  coverAttachmentId?: number
  bookingNotice?: string
}): Promise<MeetingRoom> {
  return put<MeetingRoom>(`/api/admin/meeting-rooms/${id}`, data)
}

export function updateMeetingRoomStatus(id: number, status: 'ENABLED' | 'DISABLED'): Promise<MeetingRoom> {
  return patch<MeetingRoom>(`/api/admin/meeting-rooms/${id}/status`, { status })
}

export function updateMeetingRoomOpenRules(id: number, rules: OpenRuleItem[]): Promise<{ roomId: number; rules: OpenRuleItem[] }> {
  return put(`/api/admin/meeting-rooms/${id}/open-rules`, { rules })
}

export function getMeetingRoomOpenRules(id: number): Promise<{ roomId: number; rules: OpenRuleItem[] }> {
  return get(`/api/admin/meeting-rooms/${id}/open-rules`)
}

// ── Special Date ──────────────────────────────────────────────────────────────

export function createSpecialDate(data: {
  regionCode: string
  serviceCenterId?: number
  specialDate: string
  dateType: string
  openFlag: number
  reason?: string
}): Promise<unknown> {
  return post('/api/admin/meeting-rooms/special-dates', data)
}

// ── Room Occupy ───────────────────────────────────────────────────────────────

export function createRoomOccupy(data: {
  roomId: number
  occupyTitle: string
  occupyReason?: string
  startTime: string
  endTime: string
}): Promise<unknown> {
  return post('/api/admin/meeting-rooms/occupies', data)
}

// ── Material Rules ────────────────────────────────────────────────────────────

export function getMaterialRuleList(params: {
  roomId?: number
  regionCode?: string
  serviceCenterId?: number
  enterpriseType?: string
  enabled?: number
}): Promise<MaterialRule[]> {
  return get<MaterialRule[]>('/api/admin/meeting-rooms/material-rules', params as Record<string, unknown>)
}

export function createMaterialRule(data: {
  roomId?: number
  regionCode: string
  regionName?: string
  serviceCenterId?: number
  serviceCenterName?: string
  enterpriseType?: string
  materialName: string
  materialCode: string
  requiredFlag: number
  templateAttachmentId?: number
  description?: string
  sortNo?: number
}): Promise<MaterialRule> {
  return post<MaterialRule>('/api/admin/meeting-rooms/material-rules', data)
}

export function updateMaterialRule(id: number, data: {
  regionCode?: string
  regionName?: string
  serviceCenterId?: number
  serviceCenterName?: string
  materialName?: string
  requiredFlag?: number
  templateAttachmentId?: number
  description?: string
  sortNo?: number
  enabled?: number
}): Promise<MaterialRule> {
  return put<MaterialRule>(`/api/admin/meeting-rooms/material-rules/${id}`, data)
}

export function deleteMaterialRule(id: number): Promise<unknown> {
  return del(`/api/admin/meeting-rooms/material-rules/${id}`)
}

// ── Bookings ──────────────────────────────────────────────────────────────────

export function getMeetingBookingList(params: BookingListParams): Promise<PageResult<MeetingBooking>> {
  return get<PageResult<MeetingBooking>>('/api/admin/meeting-bookings', params as Record<string, unknown>)
}

export function getMeetingBookingDetail(id: number): Promise<MeetingBooking> {
  return get<MeetingBooking>(`/api/admin/meeting-bookings/${id}`)
}

export function approveMeetingBooking(id: number, data: { auditOpinion?: string }): Promise<MeetingBooking> {
  return post<MeetingBooking>(`/api/admin/meeting-bookings/${id}/approve`, data)
}

export function rejectMeetingBooking(id: number, data: { auditOpinion: string }): Promise<MeetingBooking> {
  return post<MeetingBooking>(`/api/admin/meeting-bookings/${id}/reject`, data)
}

export function returnSupplementMeetingBooking(id: number, data: { auditOpinion: string }): Promise<MeetingBooking> {
  return post<MeetingBooking>(`/api/admin/meeting-bookings/${id}/return-supplement`, data)
}

export function completeMeetingBooking(id: number, data: {
  actualStartTime?: string
  actualEndTime?: string
  remark?: string
}): Promise<MeetingBooking> {
  return post<MeetingBooking>(`/api/admin/meeting-bookings/${id}/complete`, data)
}

export function markMeetingBookingNoShow(id: number, data: { reason?: string }): Promise<MeetingBooking> {
  return post<MeetingBooking>(`/api/admin/meeting-bookings/${id}/no-show`, data)
}

export function getMeetingBookingLedger(params: BookingListParams): Promise<PageResult<MeetingBooking>> {
  return get<PageResult<MeetingBooking>>('/api/admin/meeting-bookings/ledger', params as Record<string, unknown>)
}

export function exportMeetingBookingLedger(params: BookingListParams): Promise<unknown> {
  return get<unknown>('/api/admin/meeting-bookings/export', params as Record<string, unknown>)
}
