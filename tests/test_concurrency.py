"""
最后一轮并发整改验证：

1. 业务流水号生成（Appeal / MeetingRoomBooking / GovMeetingApply）在真实
   并发（多线程 + 各自独立数据库连接/事务）下不产生重复编号。
2. 会议室预约审批在真实并发下不会出现"同一会议室两个时间重叠的预约
   同时被通过"的情况；不同会议室的并发审批互不阻塞。

这些测试有意不使用 conftest.py 里 `db_session`/`client` 那个"单连接 +
SAVEPOINT 回滚"的隔离机制——真正的并发竞争要求多个独立连接/事务真实提交，
单一共享事务无法模拟。因此这里直接使用 `test_db_engine` 开出多个独立
Session，测试产生的数据在 `finally` 块里显式删除，不依赖事务回滚。
"""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import MeetingRoomConflictException
from app.models.appeal import AppealMain
from app.models.gov_meeting import GovMeetingApply
from app.models.meeting_room import MeetingRoom, MeetingRoomBooking
from app.utils.serial_no import generate_daily_serial


def _region():
    import secrets
    return "R" + secrets.token_hex(4)


# ── 任务一：流水号并发 ────────────────────────────────────────────────────

def _run_serial_concurrency(test_db_engine, model, column, prefix, business_type, extra_fields_factory, n=20):
    """并发生成 n 个流水号，每个线程用独立 Session/事务生成编号后立即插入
    一条最小化的真实业务行并提交——如果并发修复失效，第二个拿到重复编号
    的线程会在 INSERT 时因 unique 约束触发 IntegrityError。"""
    SessionLocal = sessionmaker(bind=test_db_engine)
    created_ids: list[int] = []
    lock = threading.Lock()

    def worker(_i):
        session = SessionLocal()
        try:
            serial = generate_daily_serial(session, model, column, prefix, business_type)
            obj = model(**extra_fields_factory(serial))
            session.add(obj)
            session.commit()
            with lock:
                created_ids.append(obj.id)
            return serial
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    try:
        with ThreadPoolExecutor(max_workers=n) as pool:
            futures = [pool.submit(worker, i) for i in range(n)]
            results = [f.result() for f in as_completed(futures)]

        assert len(results) == n
        assert len(set(results)) == n, f"生成的流水号存在重复：{results}"

        verify_session = SessionLocal()
        try:
            db_values = verify_session.query(column).filter(column.in_(results)).all()
            assert len(db_values) == n, "数据库中实际写入的业务编号数量与生成数量不一致"
        finally:
            verify_session.close()
    finally:
        cleanup = SessionLocal()
        try:
            if created_ids:
                cleanup.query(model).filter(model.id.in_(created_ids)).delete(synchronize_session=False)
                cleanup.commit()
        finally:
            cleanup.close()


def test_appeal_no_concurrency_no_duplicates(test_db_engine):
    def fields(serial):
        now = datetime.utcnow()
        return dict(
            appeal_no=serial, enterprise_id=999999999, enterprise_name="并发测试企业",
            credit_code="91TESTCONCURRENCY01", title="并发测试", content="并发测试内容",
            contact_name="测试人", contact_phone="13900000000", region_code="TESTR",
            region_name="测试区域", status="PENDING_ACCEPT", submitted_at=now,
        )
    _run_serial_concurrency(test_db_engine, AppealMain, AppealMain.appeal_no, "SQ", "APPEAL", fields)


def test_gov_meeting_apply_no_concurrency_no_duplicates(test_db_engine):
    def fields(serial):
        return dict(
            apply_no=serial, enterprise_id=999999999, enterprise_name="并发测试企业",
            credit_code="91TESTCONCURRENCY02", contact_name="测试人", contact_phone="13900000000",
            description="并发测试", commitment_checked=1, region_code="TESTR",
            region_name="测试区域", status="PENDING_AUDIT",
        )
    _run_serial_concurrency(test_db_engine, GovMeetingApply, GovMeetingApply.apply_no, "YJ", "GOV_MEETING", fields)


def test_meeting_room_booking_no_concurrency_no_duplicates(test_db_engine):
    def fields(serial):
        now = datetime.utcnow()
        return dict(
            booking_no=serial, room_id=999999999, room_name="并发测试会议室",
            enterprise_id=999999999, enterprise_name="并发测试企业", credit_code="91TESTCONCURRENCY03",
            region_code="TESTR", region_name="测试区域", meeting_subject="并发测试",
            participant_count=1, contact_name="测试人", contact_phone="13900000000",
            start_time=now + timedelta(days=3), end_time=now + timedelta(days=3, hours=1),
            status="PENDING_AUDIT", submitted_at=now,
        )
    _run_serial_concurrency(
        test_db_engine, MeetingRoomBooking, MeetingRoomBooking.booking_no, "HY", "MEETING_BOOKING", fields
    )


# ── 任务二：会议室审批并发 ──────────────────────────────────────────────────

class _RoomFixture:
    """在真实数据库中创建/清理会议室与预约测试数据（显式提交+显式清理，
    不依赖事务回滚，因为并发测试需要多个真实独立事务）。"""

    def __init__(self, test_db_engine):
        self.SessionLocal = sessionmaker(bind=test_db_engine)
        self.room_ids: list[int] = []
        self.booking_ids: list[int] = []

    def create_room(self) -> int:
        session = self.SessionLocal()
        try:
            room = MeetingRoom(
                room_name="并发测试会议室", region_code=_region(), region_name="测试区域",
                capacity=10, status="ENABLED",
            )
            session.add(room)
            session.commit()
            self.room_ids.append(room.id)
            return room.id
        finally:
            session.close()

    def create_booking(self, room_id: int, start: datetime, end: datetime) -> int:
        session = self.SessionLocal()
        try:
            now = datetime.utcnow()
            booking = MeetingRoomBooking(
                booking_no=f"HYTEST{secrets_hex()}", room_id=room_id, room_name="并发测试会议室",
                enterprise_id=999999999, enterprise_name="并发测试企业", credit_code="91TESTCONCURRENCY04",
                region_code="TESTR", region_name="测试区域", meeting_subject="并发审批测试",
                participant_count=1, contact_name="测试人", contact_phone="13900000000",
                start_time=start, end_time=end, status="PENDING_AUDIT", submitted_at=now,
            )
            session.add(booking)
            session.commit()
            self.booking_ids.append(booking.id)
            return booking.id
        finally:
            session.close()

    def get_status(self, booking_id: int) -> str:
        session = self.SessionLocal()
        try:
            return session.query(MeetingRoomBooking.status).filter(
                MeetingRoomBooking.id == booking_id
            ).scalar()
        finally:
            session.close()

    def cleanup(self):
        session = self.SessionLocal()
        try:
            if self.booking_ids:
                from app.models.meeting_room import MeetingRoomBookingAudit
                session.query(MeetingRoomBookingAudit).filter(
                    MeetingRoomBookingAudit.booking_id.in_(self.booking_ids)
                ).delete(synchronize_session=False)
                session.query(MeetingRoomBooking).filter(
                    MeetingRoomBooking.id.in_(self.booking_ids)
                ).delete(synchronize_session=False)
            if self.room_ids:
                session.query(MeetingRoom).filter(MeetingRoom.id.in_(self.room_ids)).delete(synchronize_session=False)
            from app.models.system import SysOperationLog
            session.query(SysOperationLog).filter(
                SysOperationLog.business_type == "MEETING_ROOM_BOOKING",
                SysOperationLog.business_id.in_(self.booking_ids or [-1]),
            ).delete(synchronize_session=False)
            session.commit()
        finally:
            session.close()


def secrets_hex() -> str:
    import secrets
    return secrets.token_hex(6)


def _approve_in_thread(SessionLocal, booking_id, barrier, results, idx):
    from app.services.meeting_room_service import MeetingRoomService

    session = SessionLocal()
    operator = {
        "operator_type": "USER", "operator_id": f"admin{idx}", "operator_name": f"管理员{idx}",
        "data_scope": "ALL",
    }
    barrier.wait()
    try:
        service = MeetingRoomService(session)
        detail = service.approve_booking(booking_id, {"auditOpinion": "同意"}, operator)
        results[idx] = ("OK", detail["status"])
    except Exception as e:
        session.rollback()
        results[idx] = ("ERROR", e)
    finally:
        session.close()


def test_overlapping_bookings_same_room_only_one_approved(test_db_engine):
    """同一会议室、时间重叠的两个预约被两个管理员并发审批：必须恰好一个
    APPROVED，另一个必须收到清晰的业务冲突异常，绝不能两个都通过。"""
    fixture = _RoomFixture(test_db_engine)
    try:
        for _ in range(5):
            room_id = fixture.create_room()
            base = datetime.utcnow() + timedelta(days=5)
            booking_a = fixture.create_booking(room_id, base, base + timedelta(hours=1))
            booking_b = fixture.create_booking(room_id, base + timedelta(minutes=30), base + timedelta(hours=1, minutes=30))

            barrier = threading.Barrier(2)
            results = {}
            t1 = threading.Thread(target=_approve_in_thread, args=(fixture.SessionLocal, booking_a, barrier, results, 0))
            t2 = threading.Thread(target=_approve_in_thread, args=(fixture.SessionLocal, booking_b, barrier, results, 1))
            t1.start(); t2.start()
            t1.join(timeout=30); t2.join(timeout=30)

            outcomes = [results[0], results[1]]
            oks = [o for o in outcomes if o[0] == "OK"]
            errors = [o for o in outcomes if o[0] == "ERROR"]

            assert len(oks) == 1, f"应恰好一个审批成功，实际：{outcomes}"
            assert len(errors) == 1, f"应恰好一个审批失败，实际：{outcomes}"
            assert oks[0][1] == "APPROVED"
            assert isinstance(errors[0][1], MeetingRoomConflictException), (
                f"失败的一方必须是清晰的业务冲突异常，而不是原始数据库异常：{type(errors[0][1])}"
            )

            statuses = {booking_a: fixture.get_status(booking_a), booking_b: fixture.get_status(booking_b)}
            approved_count = sum(1 for s in statuses.values() if s == "APPROVED")
            assert approved_count == 1, f"数据库中不能出现两个 APPROVED：{statuses}"
    finally:
        fixture.cleanup()


def test_different_rooms_concurrent_approval_both_succeed(test_db_engine):
    """不同会议室的预约并发审批应互不阻塞，都能成功——证明加锁粒度是
    "按会议室"而不是全局/整表锁。"""
    fixture = _RoomFixture(test_db_engine)
    try:
        room_a = fixture.create_room()
        room_b = fixture.create_room()
        base = datetime.utcnow() + timedelta(days=5)
        booking_a = fixture.create_booking(room_a, base, base + timedelta(hours=1))
        booking_b = fixture.create_booking(room_b, base, base + timedelta(hours=1))

        barrier = threading.Barrier(2)
        results = {}
        t1 = threading.Thread(target=_approve_in_thread, args=(fixture.SessionLocal, booking_a, barrier, results, 0))
        t2 = threading.Thread(target=_approve_in_thread, args=(fixture.SessionLocal, booking_b, barrier, results, 1))
        t1.start(); t2.start()
        t1.join(timeout=30); t2.join(timeout=30)

        assert results[0] == ("OK", "APPROVED"), results[0]
        assert results[1] == ("OK", "APPROVED"), results[1]
    finally:
        fixture.cleanup()
