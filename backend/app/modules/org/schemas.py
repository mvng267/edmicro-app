from datetime import date

from pydantic import BaseModel


# ---- Branches ----
class BranchCreate(BaseModel):
    name: str
    address: str | None = None


class BranchUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    status: str | None = None


class BranchOut(BaseModel):
    id: str
    name: str
    address: str | None
    status: str


# ---- Classes ----
class ClassCreate(BaseModel):
    branch_id: str
    name: str
    language: str = "en"
    level: str | None = None
    capacity: int | None = None
    start_date: date | None = None
    end_date: date | None = None


class ClassOut(BaseModel):
    id: str
    branch_id: str
    name: str
    language: str
    level: str | None
    status: str


class StaffAdd(BaseModel):
    user_id: str
    role: str  # homeroom | teacher | assistant


class StudentAdd(BaseModel):
    user_id: str


# ---- Users ----
class UserCreate(BaseModel):
    full_name: str
    role: str
    username: str | None = None
    dob: date | None = None
    email: str | None = None
    parent_phone: str | None = None
    class_id: str | None = None


class UserOut(BaseModel):
    id: str
    username: str
    full_name: str
    role: str
    status: str


class CredentialOut(BaseModel):
    id: str
    username: str
    password: str
    full_name: str


class ParentCreate(BaseModel):
    full_name: str
    parent_phone: str | None = None
    student_ids: list[str] = []


class ScopeSet(BaseModel):
    branch_ids: list[str]  # rỗng = toàn tenant
