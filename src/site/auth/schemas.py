from fastapi_users import schemas


class UserRead(schemas.BaseUser[int]):
    id: int


class UserCreate(schemas.BaseUserCreate):
    pass


