from pydantic import BaseModel
from . import Skill

class A(BaseModel):
    city:str

    def h(city):
        return f"Analyzed {city}: High Growth Potential."

SKILL=Skill("geo_analyst","Analyze city",A,h)
