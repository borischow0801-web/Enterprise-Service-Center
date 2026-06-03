import { get } from './request'

export interface DashboardSummary {
  appealTotal: number
  appealPending: number
  appealProcessing: number
  appealCompleted: number
  meetingRoomTotal: number
  meetingBookingTotal: number
  meetingBookingPending: number
  meetingBookingApproved: number
  govMeetingTotal: number
  govMeetingPending: number
  govMeetingArranged: number
  govMeetingPendingEvaluation: number
  evaluationTotal: number
  satisfiedCount: number
  unsatisfiedCount: number
}

export function getDashboardSummary() {
  return get<DashboardSummary>('/api/admin/dashboard/summary')
}
