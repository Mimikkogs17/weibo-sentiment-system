from pydantic import BaseModel
from typing import List, Dict

class LoginReq(BaseModel):
    username: str
    password: str

class SwitchReq(BaseModel):
    switch_type: str
    name: str
    endpoint: str | None = None
    version: str | None = None

class CreateTaskReq(BaseModel):
    task_name: str
    keywords: str