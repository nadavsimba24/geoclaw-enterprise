from pydantic import BaseModel
from . import Skill

class A(BaseModel):
    target:str

    def h(target):
        return f"OSINT Report for {target}: Clean."

SKILL=Skill("osint_scan","Scan target",A,h)
