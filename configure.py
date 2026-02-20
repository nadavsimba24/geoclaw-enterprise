import os
from rich.prompt import Prompt
from dotenv import set_key

if __name__ == "__main__":
    if not os.path.exists(".env"):
        open(".env", "w").close()
    key = Prompt.ask("Enter OpenAI/Provider API Key")
    set_key(".env", "OPENAI_API_KEY", key)
    print("Configuration saved.")
