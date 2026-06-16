import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .models import Note
from .storage import NoteStorage

console = Console()


def _get_storage() -> NoteStorage:
    return NoteStorage()


@click.group()
@click.version_option("0.1.0", prog_name="qnote")
def cli():
    """⚡ qnote — fast CLI note-taking for developers."""


@cli.command("add")
@click.argument("content")
@click.option("--tag", "-t", multiple=True, help="Tag(s) for the note")
def add_note(content: str, tag: tuple):
    """Add a new note."""
    storage = _get_storage()
    note = Note(content=content, tags=list(tag))
    saved = storage.add_note(note)
    tags_display = "  ".join(f"[bold cyan]#{t}[/bold cyan]" for t in saved.tags) if saved.tags else "[dim]untagged[/dim]"
    console.print(f"[green]✓[/green] Note [bold]#{saved.id}[/bold] saved   {tags_display}")


@cli.command("list")
@click.option("--tag", "-t", default=None, help="Filter by tag")
@click.option("--limit", "-n", default=20, show_default=True, help="Max notes to show")
def list_notes(tag: Optional[str], limit: int):
    """List recent notes."""
    storage = _get_storage()
    notes = storage.list_notes(tag=tag, limit=limit)
    if not notes:
        console.print("[dim]No notes found.[/dim]")
        return

    table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=5)
    table.add_column("Note", min_width=40)
    table.add_column("Tags", style="cyan")
    table.add_column("Created", style="dim", width=12)

    for n in notes:
        preview = n.content if len(n.content) <= 80 else n.content[:77] + "..."
        tags = " ".join(f"#{t}" for t in n.tags) if n.tags else ""
        created = n.created_at.strftime("%Y-%m-%d")
        table.add_row(str(n.id), preview, tags, created)

    console.print(table)
    console.print(f"[dim]Showing {len(notes)} note(s)[/dim]")


@cli.command("show")
@click.argument("note_id", type=int)
def show_note(note_id: int):
    """Show full content of a note."""
    storage = _get_storage()
    note = storage.get_note(note_id)
    if not note:
        console.print(f"[red]Note #{note_id} not found.[/red]")
        sys.exit(1)

    tags = "  ".join(f"#{t}" for t in note.tags) if note.tags else "none"
    panel = Panel(
        note.content,
        title=f"[bold]Note #{note.id}[/bold]",
        subtitle=f"[dim]{note.created_at.strftime('%Y-%m-%d %H:%M')}  tags: {tags}[/dim]",
        border_style="blue",
    )
    console.print(panel)


@cli.command("search")
@click.argument("query")
def search_notes(query: str):
    """Search notes by content."""
    storage = _get_storage()
    notes = storage.search_notes(query)
    if not notes:
        console.print(f"[dim]No notes matching '{query}'.[/dim]")
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("ID", style="dim", width=5)
    table.add_column("Note")
    table.add_column("Tags", style="cyan")

    for n in notes:
        preview = n.content if len(n.content) <= 80 else n.content[:77] + "..."
        tags = " ".join(f"#{t}" for t in n.tags) if n.tags else ""
        table.add_row(str(n.id), preview, tags)

    console.print(table)
    console.print(f"[dim]{len(notes)} result(s) for '{query}'[/dim]")


@cli.command("delete")
@click.argument("note_id", type=int)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def delete_note(note_id: int, yes: bool):
    """Delete a note by ID."""
    storage = _get_storage()
    note = storage.get_note(note_id)
    if not note:
        console.print(f"[red]Note #{note_id} not found.[/red]")
        sys.exit(1)

    if not yes:
        preview = note.content[:60] + "..." if len(note.content) > 60 else note.content
        click.confirm(f'Delete note #{note_id}: "{preview}"?', abort=True)

    storage.delete_note(note_id)
    console.print(f"[green]✓[/green] Note [bold]#{note_id}[/bold] deleted.")


@cli.command("tags")
def list_tags():
    """List all tags with note counts."""
    storage = _get_storage()
    tags = storage.get_all_tags()
    if not tags:
        console.print("[dim]No tags found.[/dim]")
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Tag", style="cyan")
    table.add_column("Notes", justify="right")

    for tag, count in tags:
        table.add_row(f"#{tag}", str(count))

    console.print(table)


@cli.command("export")
@click.option("--format", "-f", "fmt", default="md", type=click.Choice(["md", "json"]), show_default=True)
@click.option("--output", "-o", default=None, help="Output file (default: stdout)")
def export_notes(fmt: str, output: Optional[str]):
    """Export all notes to Markdown or JSON."""
    storage = _get_storage()
    notes = storage.export_all()
    if not notes:
        console.print("[dim]No notes to export.[/dim]")
        return

    if fmt == "json":
        data = [
            {
                "id": n.id,
                "content": n.content,
                "tags": n.tags,
                "created_at": n.created_at.isoformat(),
                "updated_at": n.updated_at.isoformat(),
            }
            for n in notes
        ]
        result = json.dumps(data, indent=2, ensure_ascii=False)
    else:
        lines = [f"# Notes Export — {datetime.now().strftime('%Y-%m-%d')}\n"]
        for n in notes:
            tags = ", ".join(f"`#{t}`" for t in n.tags) if n.tags else "—"
            lines.append(f"## Note #{n.id}")
            lines.append(f"**Tags:** {tags}  **Created:** {n.created_at.strftime('%Y-%m-%d %H:%M')}\n")
            lines.append(n.content)
            lines.append("\n---\n")
        result = "\n".join(lines)

    if output:
        Path(output).write_text(result, encoding="utf-8")
        console.print(f"[green]✓[/green] Exported {len(notes)} note(s) to [bold]{output}[/bold]")
    else:
        print(result)
