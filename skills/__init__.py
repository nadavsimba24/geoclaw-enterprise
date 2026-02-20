import importlib, os

class Skill:
    def __init__(self, name, d, schema, h):
        self.name, self.description, self.args_schema, self.handler = name, d, schema, h

    def to_openai_tool(self):
        return {"type":"function","function":{"name":self.name,"description":self.description,"parameters":self.args_schema.schema()}}

def load_skills():
    s={}
    for f in os.listdir(os.path.dirname(__file__)):
        if f.endswith(".py") and f!="__init__.py":
            m=importlib.import_module(f"skills.{f[:-3]}")
            if hasattr(m,"SKILL"):
                s[m.SKILL.name]=m.SKILL
    return s
