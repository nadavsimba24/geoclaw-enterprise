from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Label, TabbedContent, TabPane, Markdown
from textual import work
from main import GeoclawCore

class GeoclawTUI(App):
    CSS = "Screen { background: #0f172a; color: white; } Input { dock: bottom; }"

    def compose(self) -> ComposeResult:
        self.bot = GeoclawCore()
        yield Header()
        with TabbedContent():
            with TabPane("Chat"):
                yield Label(id="chat_out"); yield Input(id="chat_in")
            with TabPane("Geo-Intel"):
                yield Label("Geo Module Ready")
        yield Footer()

    async def on_input_submitted(self, m):
        self.query_one("#chat_out").update(f"Thinking...")
        self.run_bot(m.value)
        m.input.value = ""

    @work
    async def run_bot(self, txt):
        res = self.bot.run(txt)
        self.call_from_thread(self.query_one("#chat_out").update, res)

if __name__ == "__main__":
    GeoclawTUI().run()
