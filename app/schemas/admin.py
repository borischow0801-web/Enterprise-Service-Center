from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class AdminUserInfo(BaseModel):
    id: int
    platformUserId: str
    username: str
    realName: str
    mobile: Optional[str] = None
    departmentId: str
    departmentName: str
    regionCode: str
    regionName: str
    roleCodes: List[str]
    dataScope: str
    lastLoginTime: Optional[datetime] = None

    model_config = {"from_attributes": True}
