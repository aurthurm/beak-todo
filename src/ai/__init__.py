"""AI command group for Felicity Todos."""

import typer

from src.ai import commands

ai_app = typer.Typer(help="AI-powered todo features")
ai_app.add_typer(commands.provider_app, name="provider")

ai_app.command("setup")(commands.setup)
ai_app.command("doctor")(commands.doctor)
ai_app.command("add")(commands.add)
ai_app.command("plan")(commands.plan)
ai_app.command("summary")(commands.summary)
ai_app.command("search")(commands.ai_search)
ai_app.command("breakdown")(commands.breakdown)
ai_app.command("risks")(commands.risks)
ai_app.command("chat")(commands.chat)
ai_app.command("email")(commands.email)
