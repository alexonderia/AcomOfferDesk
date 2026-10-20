from pydantic import BaseModel, Field, field_validator

from app.schemas.actions import UnitActionsSchema


class UnitMemberSchema(BaseModel):
    user_id: str
    full_name: str | None = None
    role_id: int
    role_name: str
    status: str
    id_parent_user: str | None = None


class AvailableUnitUserSchema(BaseModel):
    user_id: str
    full_name: str | None = None
    role_id: int
    role_name: str
    status: str


class UnitNodeSchema(BaseModel):
    unit_id: int
    name: str
    id_parent: int | None = None
    is_active: bool
    members: list[UnitMemberSchema] = Field(default_factory=list)
    children: list["UnitNodeSchema"] = Field(default_factory=list)
    actions: UnitActionsSchema = Field(default_factory=UnitActionsSchema)


class UnitTreeData(BaseModel):
    items: list[UnitNodeSchema] = Field(default_factory=list)


class UnitTreeResponse(BaseModel):
    data: UnitTreeData


class RecommendedHierarchyNodeSchema(BaseModel):
    user_id: str
    full_name: str | None = None
    role_id: int
    role_name: str
    status: str
    id_parent_user: str | None = None
    children: list["RecommendedHierarchyNodeSchema"] = Field(default_factory=list)


class RecommendedHierarchyData(BaseModel):
    items: list[RecommendedHierarchyNodeSchema] = Field(default_factory=list)


class RecommendedHierarchyResponse(BaseModel):
    data: RecommendedHierarchyData


class UnitMutationResponse(BaseModel):
    data: UnitNodeSchema


class CreateUnitRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    id_parent: int | None = Field(default=None, ge=1)

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Название должно быть строкой")
        normalized = value.strip()
        if not normalized:
            raise ValueError("Название юнита обязательно")
        return normalized


class UpdateUnitRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    id_parent: int | None = Field(default=None, ge=1)

    @field_validator("name", mode="before")
    @classmethod
    def _strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("Название должно быть строкой")
        normalized = value.strip()
        if not normalized:
            raise ValueError("Название юнита обязательно")
        return normalized


class AddUnitMemberRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=255)

    @field_validator("user_id", mode="before")
    @classmethod
    def _strip_user_id(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Идентификатор пользователя должен быть строкой")
        normalized = value.strip()
        if not normalized:
            raise ValueError("Идентификатор пользователя обязателен")
        return normalized


class UnitMemberResponse(BaseModel):
    data: UnitMemberSchema


class UnitMembersData(BaseModel):
    items: list[UnitMemberSchema] = Field(default_factory=list)


class UnitMembersResponse(BaseModel):
    data: UnitMembersData


class AvailableUnitUsersData(BaseModel):
    items: list[AvailableUnitUserSchema] = Field(default_factory=list)


class AvailableUnitUsersResponse(BaseModel):
    data: AvailableUnitUsersData
