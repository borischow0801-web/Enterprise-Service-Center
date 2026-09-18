"""按日流水号生成：前缀 + yyyyMMdd + 4位序号。

并发安全设计（替代原先的"查询当日最大值再 +1"，该方式在多 worker/多容器
下存在竞态：两个事务并发查询到同一个最大值，各自 +1 后生成重复编号）。

改为基于 sys_daily_serial 计数表的原子自增，拆成两步：

  1. _ensure_counter_row：确保 (business_type, business_date) 这一行存在，
     不存在则以"历史业务表中当日已有编号的最大末四位"作为起始值——只在
     系统首次为某个 (business_type, 日期) 生成编号时才会真正插入新行（例
     如本次改造上线当天，此前旧逻辑可能已生成过一些编号），此后每天该行
     只会被创建一次，不影响历史编号、不改写历史数据。

     这一步刻意使用一条独立于调用方事务的、立即提交的连接/事务完成，
     不占用调用方 db 会话的事务——原因：如果把 INSERT IGNORE 和后面的
     UPDATE 放在同一个长事务里，当同一天第一次出现多个并发请求时，多个
     事务同时争抢插入同一个尚不存在的唯一键会触发 InnoDB 死锁检测
     （errno 1213）；而死锁发生后 InnoDB 会整体回滚"受害"事务，不是只回
     滚到某个 SAVEPOINT，因此不可能在不影响调用方已有写入的前提下，在同
     一个共享事务里做局部重试。把这一步单独放进一条自己的、立即提交的连
     接，即使个别请求在这极短的窗口内偶尔遇到瞬时锁冲突，也可以安全地整
     体重试（不影响任何其他数据），冲突窗口从"整个业务事务"缩短到"一条
     INSERT 语句"，实测可稳定消除该死锁。

  2. UPDATE ... SET current_value = LAST_INSERT_ID(current_value + 1)
     对已存在的行做原子自增并通过 LAST_INSERT_ID() 读回新值——这是 MySQL
     官方文档推荐的、不依赖应用层锁的序列表实现方式
     （https://dev.mysql.com/doc/refman/8.0/en/example-auto-increment.html）。
     这一步在调用方 db 会话的事务里执行：该 UPDATE 对这一行加排他锁，锁
     会保持到调用方所在事务提交/回滚为止，从而保证"生成编号"与"用该编号
     写入业务行并提交"之间不会被其他并发事务插队产生重复编号。这一步只
     会对一个已确定存在的行做单行 UPDATE，不存在"插入不存在的键"那类死
     锁场景，因此不需要重试。不同 (business_type, business_date) 之间互不
     阻塞，不同业务模块、跨天的请求完全并行。
"""
from datetime import date as date_type, datetime
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

_RETRYABLE_MYSQL_ERRNOS = {1213, 1205}  # Deadlock found / Lock wait timeout exceeded
_MAX_ATTEMPTS = 3


def _max_existing_suffix(db: Session, column, full_prefix: str) -> int:
    """历史兼容：仅在 sys_daily_serial 尚无该 (business_type, 日期) 行时使用，
    扫描业务表中当日已有编号的最大末四位，避免与改造上线当天、迁移之前
    已生成的编号发生冲突。不修改任何历史数据。"""
    rows = db.query(column).filter(column.like(f"{full_prefix}%")).all()
    max_seq = 0
    for (no,) in rows:
        if not no or not no.startswith(full_prefix):
            continue
        tail = no[len(full_prefix):]
        if len(tail) >= 4 and tail[:4].isdigit():
            max_seq = max(max_seq, int(tail[:4]))
        elif tail.isdigit() and len(tail) <= 4:
            max_seq = max(max_seq, int(tail))
    return max_seq


def _ensure_counter_row(db: Session, business_type: str, business_date: date_type, seed: int) -> None:
    """用独立于调用方事务的连接，立即提交地确保计数行存在。见模块顶部说明。

    db.get_bind() 在生产环境（Session 直接绑定 Engine）下返回 Engine；在本项目
    测试环境（tests/conftest.py 里 Session 绑定的是某个具体 Connection，用于
    SAVEPOINT 回滚隔离）下返回的是 Connection——两种情况都统一取到其 Engine，
    才能 .connect() 开出一条真正独立、不受调用方事务影响的新连接。
    """
    bind = db.get_bind()
    engine = bind if isinstance(bind, Engine) else bind.engine
    last_error: OperationalError | None = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            with engine.connect() as conn:
                conn.execute(
                    text(
                        "INSERT IGNORE INTO sys_daily_serial (business_type, business_date, current_value) "
                        "VALUES (:business_type, :business_date, :seed)"
                    ),
                    {"business_type": business_type, "business_date": business_date, "seed": seed},
                )
                conn.commit()
            return
        except OperationalError as e:
            errno = e.orig.args[0] if getattr(e, "orig", None) and e.orig.args else None
            if errno in _RETRYABLE_MYSQL_ERRNOS and attempt < _MAX_ATTEMPTS - 1:
                last_error = e
                continue
            raise
    raise last_error  # pragma: no cover - unreachable, loop always returns or raises


def generate_daily_serial(db: Session, model, column, prefix: str, business_type: str) -> str:
    """
    生成格式：{prefix}{yyyyMMdd}{4位流水}，例如 SQ202605290001。
    business_type 是 sys_daily_serial 计数表中的分类键（如 "APPEAL"），
    与 prefix（编号前缀，如 "SQ"）分开维护，便于计数表可读性。
    """
    now = datetime.utcnow()
    date_str = now.strftime("%Y%m%d")
    full_prefix = f"{prefix}{date_str}"
    business_date = now.date()

    seed = _max_existing_suffix(db, column, full_prefix)
    _ensure_counter_row(db, business_type, business_date, seed)

    db.execute(
        text(
            "UPDATE sys_daily_serial SET current_value = LAST_INSERT_ID(current_value + 1) "
            "WHERE business_type = :business_type AND business_date = :business_date"
        ),
        {"business_type": business_type, "business_date": business_date},
    )
    next_seq = db.execute(text("SELECT LAST_INSERT_ID()")).scalar()
    return f"{full_prefix}{int(next_seq):04d}"
