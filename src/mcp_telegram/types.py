from pydantic import BaseModel


class Contact(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    phone: str | None = None
