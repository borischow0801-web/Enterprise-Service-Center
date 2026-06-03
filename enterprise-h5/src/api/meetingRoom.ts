import { get, post } from './request'
import { apiAssetUrl } from '@/utils/api'

// ── Interfaces ────────────────────────────────────────────────────────────────

export interface MeetingRoom {
  id: number
  roomName: string
  roomType?: string
  roomTypeName?: string
  regionCode: string
  regionName: string
  serviceCenterId?: number
  serviceCenterName?: string
  address?: string
  capacity: number
  facilities?: string[]
  description?: string
  coverAttachmentId?: number
  coverImageUrl?: string
  images?: { attachmentId: number; url: string; isCover: number; sortNo: number }[]
  bookingNotice?: string
  status: string
  openRules?: OpenRule[]
  materialRules?: MaterialRule[]
  // snake_case compat
  room_name?: string
  cover_image_url?: string
  service_center_name?: string
}

export interface OpenRule {
  weekday: number
  openFlag: number
  open_flag?: number
  startTime?: string
  endTime?: string
  start_time?: string
  end_time?: string
}

export interface MaterialRule {
  id: number
  materialName: string
  material_name?: string
  materialCode: string
  material_code?: string
  requiredFlag: number
  required_flag?: number
  templateAttachmentId?: number
  template_attachment_id?: number
  templateDownloadUrl?: string
  description?: string
  sortNo?: number
}

export interface RoomCalendar {
  roomId: number
  startDate: string
  endDate: string
  bookedSlots: { bookingId: number; startTime: string; endTime: string; status: string }[]
  occupiedSlots: { occupyId: number; title: string; startTime: string; endTime: string }[]
  specialDates: { date: string; dateType: string; openFlag: number; reason?: string }[]
  openRules: OpenRule[]
}

export interface MeetingBooking {
  id: number
  bookingNo: string
  booking_no?: string
  roomId: number
  room_id?: number
  roomName: string
  room_name?: string
  enterpriseName: string
  enterprise_name?: string
  meetingSubject: string
  meeting_subject?: string
  participantCount: number
  participant_count?: number
  contactName: string
  contact_name?: string
  contactPhone: string
  contact_phone?: string
  startTime: string
  start_time?: string
  endTime: string
  end_time?: string
  supportItems?: string[]
  support_items?: string[]
  status: string
  cancelReason?: string
  cancel_reason?: string
  submittedAt?: string
  submitted_at?: string
  createdAt?: string
  created_at?: string
  attachments?: { id: number; originalName: string; fileExt: string; fileSize: number }[]
  auditRecords?: BookingAuditRecord[]
  actualStartTime?: string
  actualEndTime?: string
  completedRemark?: string
  enterpriseType?: string
  enterprise_type?: string
  materials?: BookingMaterialItem[]
}

export interface BookingMaterialItem {
  materialCode: string
  material_code?: string
  materialName?: string
  material_name?: string
  requiredFlag?: number
  required_flag?: number
  description?: string
  attachments?: { id: number; originalName: string; fileSize?: number }[]
}

export interface BookingAuditRecord {
  id: number
  actionType?: string
  action?: string
  actionName?: string
  action_name?: string
  auditOpinion?: string
  opinion?: string
  beforeStatus?: string
  afterStatus?: string
  operatorName?: string
  operator_name?: string
  operatorDeptName?: string
  operator_dept_name?: string
  createdAt: string
  created_at?: string
}

export interface PageResult<T> {
  records: T[]
  total: number
  pageNo: number
  pageSize: number
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/** camelCase / snake_case compat field accessor */
export function rn(room: MeetingRoom): string {
  return room.roomName || room.room_name || ''
}
export function coverUrl(room: MeetingRoom): string {
  const raw = room.coverImageUrl || room.cover_image_url || ''
  return apiAssetUrl(raw)
}
export function bn(booking: MeetingBooking): string {
  return booking.bookingNo || booking.booking_no || ''
}
export function ms(booking: MeetingBooking): string {
  return booking.meetingSubject || booking.meeting_subject || ''
}
export function st(booking: MeetingBooking): string {
  return booking.startTime || booking.start_time || ''
}
export function et(booking: MeetingBooking): string {
  return booking.endTime || booking.end_time || ''
}
export function matName(rule: MaterialRule): string {
  return rule.materialName || rule.material_name || ''
}
export function matCode(rule: MaterialRule): string {
  return rule.materialCode || rule.material_code || ''
}
export function matRequired(rule: MaterialRule): number {
  return rule.requiredFlag ?? rule.required_flag ?? 0
}
export function matTplId(rule: MaterialRule): number | undefined {
  return rule.templateAttachmentId ?? rule.template_attachment_id
}

// ── Meeting Room APIs ─────────────────────────────────────────────────────────

export function getMeetingRooms(params: {
  regionCode?: string
  capacityMin?: number
  facility?: string
  roomType?: string
  pageNo?: number
  pageSize?: number
}): Promise<PageResult<MeetingRoom>> {
  return get<PageResult<MeetingRoom>>('/api/enterprise/meeting-rooms', params as Record<string, unknown>)
}

export function getMeetingRoomDetail(id: number): Promise<MeetingRoom> {
  return get<MeetingRoom>(`/api/enterprise/meeting-rooms/${id}`)
}

export function getMeetingRoomCalendar(id: number, params: {
  startDate: string
  endDate: string
}): Promise<RoomCalendar> {
  return get<RoomCalendar>(`/api/enterprise/meeting-rooms/${id}/calendar`, params as Record<string, unknown>)
}

export function getMeetingRoomMaterialRules(id: number, params?: {
  enterpriseType?: string
}): Promise<MaterialRule[]> {
  return get<MaterialRule[]>(`/api/enterprise/meeting-rooms/${id}/material-rules`, params as Record<string, unknown>)
}

// ── Booking APIs ──────────────────────────────────────────────────────────────

export interface BookingMaterialPayload {
  materialCode: string
  materialName?: string
  attachmentIds: number[]
}

export function createMeetingBooking(data: {
  roomId: number
  meetingSubject: string
  participantCount: number
  contactName: string
  contactPhone: string
  startTime: string
  endTime: string
  enterpriseType: string
  supportItems?: string[]
  materials?: BookingMaterialPayload[]
  attachmentIds?: number[]
}): Promise<MeetingBooking> {
  return post<MeetingBooking>('/api/enterprise/meeting-bookings', data)
}

export function getMyMeetingBookings(params: {
  status?: string
  pageNo?: number
  pageSize?: number
}): Promise<PageResult<MeetingBooking>> {
  return get<PageResult<MeetingBooking>>('/api/enterprise/meeting-bookings', params as Record<string, unknown>)
}

export function getMeetingBookingDetail(id: number): Promise<MeetingBooking> {
  return get<MeetingBooking>(`/api/enterprise/meeting-bookings/${id}`)
}

/** 取消预约：POST /api/enterprise/meeting-bookings/{id}/cancel */
export function cancelMeetingBooking(id: number, data: { cancelReason: string }): Promise<MeetingBooking> {
  return post<MeetingBooking>(`/api/enterprise/meeting-bookings/${id}/cancel`, data)
}

/** 补充材料：POST /api/enterprise/meeting-bookings/{id}/supplement */
export function supplementMeetingBooking(
  id: number,
  data: {
    materials?: BookingMaterialPayload[]
    attachmentIds?: number[]
    remark?: string
  },
): Promise<MeetingBooking> {
  return post<MeetingBooking>(`/api/enterprise/meeting-bookings/${id}/supplement`, data)
}
