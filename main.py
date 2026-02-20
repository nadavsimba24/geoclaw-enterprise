import os, yaml, json
from dotenv import load_dotenv
from openai import OpenAI
from skills import load_skills

load_dotenv()

class GeoclawCore:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("BASE_URL"))
        self.skills = load_skills()
        self.model = os.getenv("MODEL_NAME", "gpt-4-turbo")
        self.history = [{"role": "system", "content": "You are an enterprise intelligence agent."}]

    def run(self, txt):
        self.history.append({"role": "user", "content": txt})
        tools = [s.to_openai_tool() for s in self.skills.values()]
        try:
            res = self.client.chat.completions.create(model=self.model, messages=self.history, tools=tools)
            msg = res.choices[0].message
            if msg.tool_calls:
                self.history.append(msg)
                for tc in msg.tool_calls:
                    res_txt = self.skills[tc.function.name].handler(**json.loads(tc.function.arguments))
                    self.history.append({"role": "tool", "tool_call_id": tc.id, "name": tc.function.name, "content": str(res_txt)})
                return self.run(txt)  # Recursion for simplicity in this snippet

            self.history.append({"role": "assistant", "content": msg.content})
            return msg.content
        except Exception as e:
            return f"Error: {e}"
