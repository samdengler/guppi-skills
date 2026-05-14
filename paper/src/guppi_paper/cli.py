"""GUPPI paper skill CLI"""

import subprocess
from pathlib import Path
from typing import Annotated

import typer

from guppi_paper import __version__
from guppi_paper.template import hydrate


def _version_callback(value: bool):
    if value:
        typer.echo(f"guppi-paper {__version__}")
        raise typer.Exit()


app = typer.Typer(help="Analyze academic papers using the Feynman Technique")


@app.callback()
def main(
    version: Annotated[bool, typer.Option("--version", "-V", help="Show version and exit", callback=_version_callback, is_eager=True)] = False,
):
    pass


# --- Domain commands ---


@app.command()
def prompt(
    source: Annotated[str, typer.Argument(help="URL or local file path of the paper")],
):
    """Output the hydrated Feynman Technique analysis prompt for a paper."""
    path = Path(source)
    if path.is_file():
        if path.suffix == ".pdf":
            try:
                result = subprocess.run(
                    ["pdftotext", str(path), "-"],
                    capture_output=True, text=True, check=True,
                )
            except FileNotFoundError:
                typer.echo("Error: pdftotext not found. Install with: brew install poppler", err=True)
                raise typer.Exit(1)
            content = result.stdout
        else:
            content = path.read_text()
        typer.echo(hydrate(source, content=content))
    else:
        typer.echo(hydrate(source))


@app.command()
def pdf(
    markdown_file: Annotated[Path, typer.Argument(help="Path to the markdown analysis file to convert")],
):
    """Convert a markdown analysis file to PDF via pandoc."""
    if not markdown_file.exists():
        typer.echo(f"Error: file not found: {markdown_file}", err=True)
        raise typer.Exit(1)

    output_pdf = markdown_file.with_suffix(".pdf")

    try:
        subprocess.run(
            [
                "pandoc",
                str(markdown_file),
                "-o", str(output_pdf),
                "--pdf-engine=xelatex",
                "-V", "geometry:margin=1in",
                "-V", "fontsize=11pt",
                "--highlight-style=tango",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        typer.echo("Error: pandoc not found. Install with: brew install pandoc basictex", err=True)
        raise typer.Exit(1)
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error: pandoc conversion failed: {e.stderr}", err=True)
        raise typer.Exit(1)

    typer.echo(str(output_pdf))


# --- Skill management subcommand group ---

skill_app = typer.Typer(help="Skill management commands")
app.add_typer(skill_app, name="skill")


@skill_app.command()
def install():
    """Register this skill with guppi-cli."""
    skill_md = _get_skill_md_path()
    skill_dir = skill_md.parent
    result = subprocess.run(
        ["guppi", "skills", "install", "paper", "--from", str(skill_dir), "--yes"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        typer.echo(result.stdout.strip())
    else:
        typer.echo(f"Error: {result.stderr.strip()}", err=True)
        raise typer.Exit(1)


@skill_app.command()
def show():
    """Display SKILL.md contents."""
    skill_md = _get_skill_md_path()
    typer.echo(skill_md.read_text())


def _get_skill_md_path() -> Path:
    """Locate SKILL.md bundled in the package."""
    package_dir = Path(__file__).parent
    skill_md = package_dir / "SKILL.md"
    if not skill_md.exists():
        # Fallback: look in the skill root (development mode)
        # package_dir = paper/src/guppi_paper → .parent.parent = paper/
        skill_md = package_dir.parent.parent / "SKILL.md"
    if not skill_md.exists():
        typer.echo("Error: SKILL.md not found", err=True)
        raise typer.Exit(1)
    return skill_md


if __name__ == "__main__":
    app()
