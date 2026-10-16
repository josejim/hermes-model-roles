"""Hermes Model Roles package entrypoint."""
from .cli import handle_slash_command

def setup(context):
    """Registers /roles command in Hermes."""
    context.register_command("roles", handle_slash_command, description="Manage and query centralized model roles")
