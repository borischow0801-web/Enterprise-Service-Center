from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional

from app.core.password import assert_password_strength
from app.core.validators import validate_credit_code, validate_mobile


class EnterpriseRegisterRequest(BaseModel):
    enterpriseName: str = Field(..., min_length=1, max_length=200, description="企业名称")
    creditCode: str = Field(..., description="统一社会信用代码")
    contactName: str = Field(..., min_length=1, max_length=100, description="联系人姓名")
    contactMobile: str = Field(..., description="联系手机号")
    password: str = Field(..., description="密码")
    confirmPassword: str = Field(..., description="确认密码")

    @field_validator("creditCode")
    @classmethod
    def _check_credit_code(cls, v: str) -> str:
        return validate_credit_code(v)

    @field_validator("contactMobile")
    @classmethod
    def _check_mobile(cls, v: str) -> str:
        return validate_mobile(v)

    @field_validator("password")
    @classmethod
    def _check_password_strength(cls, v: str) -> str:
        return assert_password_strength(v)

    @model_validator(mode="after")
    def _check_password_match(self) -> "EnterpriseRegisterRequest":
        if self.password != self.confirmPassword:
            raise ValueError("两次输入的密码不一致")
        return self


class EnterpriseLoginRequest(BaseModel):
    creditCode: str = Field(..., description="统一社会信用代码")
    password: str = Field(..., min_length=1, max_length=128, description="密码")

    @field_validator("creditCode")
    @classmethod
    def _check_credit_code(cls, v: str) -> str:
        return validate_credit_code(v)


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
