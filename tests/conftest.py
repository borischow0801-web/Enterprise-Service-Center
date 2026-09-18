"""
Pytest infrastructure for the full regression suite (B1).

Design decision: run against the real, already-migrated MySQL 8 database
configured via `.env` (`settings.database_url`) — NOT SQLite. SQLite and
MySQL 8 differ in ways that matter for this app (BigInteger PK autoincrement
aliasing, locking semantics, SQL dialect quirks), and this project's own
review explicitly calls for tests that represent actual MySQL behaviour
rather than convenient-but-unfaithful SQLite substitutes. No database
address is hardcoded here — the connection comes entirely from the app's own
settings, the same ones the app itself uses to run.

Tests must not leave any trace in that database. Rather than provisioning a
separate "<db>_test" database (the configured DB user does not have
CREATE DATABASE privilege — a realistic least-privilege setup, confirmed at
runtime), isolation is achieved purely at the transaction level: each test
runs inside a SAVEPOINT that is unconditionally rolled back afterwards (the
standard SQLAlchemy "join a session into an external transaction" recipe).
Application code calling `session.commit()` only releases/restarts the
SAVEPOINT; the outer transaction — and therefore everything written during
the test — is discarded when the test ends, pass or fail.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import get_db


@pytest.fixture(scope="session")
def test_db_engine():
    # pool_size/max_overflow 加大：本轮新增的真实并发测试（tests/test_concurrency.py）
    # 需要同时开出多个独立连接模拟多个独立事务，且 app/utils/serial_no.py 的
    # 计数行兜底逻辑每次调用还会额外借用一条独立连接——默认的 5+10 在 20 个
    # 线程并发下会耗尽连接池，属于测试基础设施容量问题，与业务代码无关。
    engine = create_engine(settings.database_url, pool_pre_ping=True, pool_size=20, max_overflow=40)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(test_db_engine):
    connection = test_db_engine.connect()
    trans = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess, transaction):
        if transaction.nested and not transaction._parent.nested:
            sess.begin_nested()

    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        connection.close()


@pytest.fixture()
def client(db_session):
    from app.main import app

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def as_production_env():
    """Temporarily flips settings.app_env to 'production' for the duration of a test."""
    original = settings.app_env
    settings.app_env = "production"
    try:
        yield
    finally:
        settings.app_env = original


@pytest.fixture(autouse=True)
def _ensure_dev_env():
    """Guard against test pollution: force development env before each test unless
    the test explicitly opts into as_production_env."""
    original = settings.app_env
    settings.app_env = "development"
    yield
    settings.app_env = original


@pytest.fixture(autouse=True)
def _cleanup_uploaded_files():
    """Attachment uploads write to disk directly (not part of any DB transaction),
    so the SAVEPOINT rollback in `db_session` cannot undo them. Tests that exercise
    the real upload endpoint (see §三十一 attachment tests) would otherwise leave an
    ever-growing pile of orphan files in uploads/attachments/ on every run. This
    snapshots the directory before each test and removes anything new afterwards."""
    upload_dir = os.path.join(settings.upload_dir_resolved, "attachments")
    before = set(os.listdir(upload_dir)) if os.path.isdir(upload_dir) else set()
    yield
    if os.path.isdir(upload_dir):
        after = set(os.listdir(upload_dir))
        for name in after - before:
            try:
                os.remove(os.path.join(upload_dir, name))
            except OSError:
                pass
