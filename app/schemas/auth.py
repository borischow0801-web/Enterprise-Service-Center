from pydantic import BaseModel, Field
from typing import Optional


class EnterpriseMockLoginRequest(BaseModel):
    enterpriseName: str = Field(..., description="企业名称")
    creditCode: str = Field(..., description="统一社会信用代码")
    legalPersonName: str = Field(..., description="法人姓名")
    legalPersonIdNo: str = Field(..., description="法人身份证号")
    legalPersonMobile: str = Field(..., description="法人手机号")


class AdminMockLoginRequest(BaseModel):
    platformUserId: str = Field(..., description="平台用户ID")
    username: str = Field(..., description="用户名")
    realName: str = Field(..., description="真实姓名")
    departmentId: str = Field(..., description="部门ID")
    departmentName: str = Field(..., description="部门名称")
    regionCode: str = Field(..., description="行政区划代码")
    regionName: str = Field(..., description="行政区划名称")
    roleCodes: list[str] = Field(..., description="角色编码列表")
    dataScope: str = Field(..., description="数据权限范围")


class TokenResponse(BaseModel):
    accessToken: str
    tokenType: str = "Bearer"
    expiresIn: int  # seconds
