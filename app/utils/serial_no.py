"""按日流水号生成：前缀 + yyyyMMdd + 4位序号。"""
from datetime import datetime
from sqlalchemy.orm import Session


def generate_daily_serial(db: Session, model, column, prefix: str) -> str:
    """
    生成格式：{prefix}{yyyyMMdd}{4位流水}，例如 SQ202605290001。
    仅统计当日同前缀编号的最大末四位，不修改历史数据。
    """
    date_str = datetime.utcnow().strftime("%Y%m%d")
    full_prefix = f"{prefix}{date_str}"
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
    return f"{full_prefix}{max_seq + 1:04d}"
