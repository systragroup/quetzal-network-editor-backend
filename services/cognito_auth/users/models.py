from pydantic import BaseModel


class User(BaseModel):
	username: str
	given_name: str | None = None
	family_name: str | None = None
	email: str | None = None
	password: str


class Username(BaseModel):
	username: str
