"""管理端工作台基础统计"""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.constants.appeal import AppealStatus
from app.constants.meeting_room import BookingStatus
from app.constants.gov_meeting import GovMeetingStatus
from app.models.appeal import AppealMain
from app.models.meeting_room import MeetingRoom, MeetingRoomBooking
from app.models.gov_meeting import GovMeetingApply
from app.models.system import SysEvaluation


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def _appeal_query(self, data_scope: str, region_code: str, dept_id: str):
        q = self.db.query(AppealMain)
        if data_scope == "REGION" and region_code:
            q = q.filter(AppealMain.region_code == region_code)
        elif data_scope in ("DEPARTMENT", "SELF") and dept_id:
            q = q.filter(AppealMain.responsible_dept_id == dept_id)
        return q

    def _booking_query(self, data_scope: str, region_code: str):
        q = self.db.query(MeetingRoomBooking).filter(MeetingRoomBooking.deleted_flag == 0)
        if data_scope == "REGION" and region_code:
            q = q.filter(MeetingRoomBooking.region_code == region_code)
        return q

    def _room_query(self, data_scope: str, region_code: str):
        q = self.db.query(MeetingRoom).filter(MeetingRoom.deleted_flag == 0)
        if data_scope == "REGION" and region_code:
            q = q.filter(MeetingRoom.region_code == region_code)
        return q

    def _gov_query(self, data_scope: str, region_code: str):
        q = self.db.query(GovMeetingApply).filter(GovMeetingApply.deleted_flag == 0)
        if data_scope == "REGION" and region_code:
            q = q.filter(GovMeetingApply.region_code == region_code)
        return q

    def get_summary(self, data_scope: str, region_code: str, dept_id: str) -> dict:
        appeal_q = self._appeal_query(data_scope, region_code, dept_id)
        processing_statuses = [
            AppealStatus.ACCEPTED,
            AppealStatus.CENTER_HANDLING,
            AppealStatus.DEPT_HANDLING,
            AppealStatus.CENTER_REVIEWING,
        ]
        completed_statuses = [AppealStatus.EVALUATED, AppealStatus.COMPLETED]

        appeal_total = appeal_q.count()
        appeal_pending = appeal_q.filter(AppealMain.status == AppealStatus.PENDING_ACCEPT).count()
        appeal_processing = appeal_q.filter(AppealMain.status.in_(processing_statuses)).count()
        appeal_completed = appeal_q.filter(AppealMain.status.in_(completed_statuses)).count()

        room_q = self._room_query(data_scope, region_code)
        booking_q = self._booking_query(data_scope, region_code)
        meeting_room_total = room_q.count()
        meeting_booking_total = booking_q.count()
        meeting_booking_pending = booking_q.filter(
            MeetingRoomBooking.status == BookingStatus.PENDING_AUDIT
        ).count()
        meeting_booking_approved = booking_q.filter(
            MeetingRoomBooking.status.in_([
                BookingStatus.APPROVED,
                BookingStatus.WAIT_USE,
                BookingStatus.COMPLETED,
            ])
        ).count()

        gov_q = self._gov_query(data_scope, region_code)
        gov_meeting_total = gov_q.count()
        gov_meeting_pending = gov_q.filter(
            GovMeetingApply.status == GovMeetingStatus.PENDING_AUDIT
        ).count()
        gov_meeting_arranged = gov_q.filter(
            GovMeetingApply.status.in_([
                GovMeetingStatus.ARRANGED,
                GovMeetingStatus.WAIT_MEETING,
            ])
        ).count()
        gov_meeting_pending_evaluation = gov_q.filter(
            GovMeetingApply.status == GovMeetingStatus.PENDING_EVALUATION
        ).count()

        eval_q = self.db.query(SysEvaluation).filter(SysEvaluation.deleted_flag == 0)
        evaluation_total = eval_q.count()
        satisfied_count = eval_q.filter(SysEvaluation.satisfaction == "SATISFIED").count()
        unsatisfied_count = eval_q.filter(SysEvaluation.satisfaction == "UNSATISFIED").count()

        return {
            "appealTotal": appeal_total,
            "appealPending": appeal_pending,
            "appealProcessing": appeal_processing,
            "appealCompleted": appeal_completed,
            "meetingRoomTotal": meeting_room_total,
            "meetingBookingTotal": meeting_booking_total,
            "meetingBookingPending": meeting_booking_pending,
            "meetingBookingApproved": meeting_booking_approved,
            "govMeetingTotal": gov_meeting_total,
            "govMeetingPending": gov_meeting_pending,
            "govMeetingArranged": gov_meeting_arranged,
            "govMeetingPendingEvaluation": gov_meeting_pending_evaluation,
            "evaluationTotal": evaluation_total,
            "satisfiedCount": satisfied_count,
            "unsatisfiedCount": unsatisfied_count,
        }
