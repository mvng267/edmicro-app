from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    must_change_password: bool


class MeResponse(BaseModel):
    user_id: str
    tenant_id: str
    role: str
