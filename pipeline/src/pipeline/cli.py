"""CLI entry point for the Noir Canvas pipeline."""

import click

from pipeline.commands import (
    analyze_frames,
    artist_studio,
    avatar,
    create_artist,
    curate,
    frame,
    full,
    generate,
    mockup,
    process_images,
    register,
    room_mockup,
    room_templates_group,
    standardise,
    upscale,
)


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """Noir Canvas AI art generation pipeline."""


cli.add_command(create_artist)
cli.add_command(generate)
cli.add_command(curate)
cli.add_command(upscale)
cli.add_command(avatar)
cli.add_command(artist_studio)
cli.add_command(full)
cli.add_command(process_images)
cli.add_command(standardise)
cli.add_command(analyze_frames)
cli.add_command(frame)
cli.add_command(room_mockup)
cli.add_command(room_templates_group)
cli.add_command(mockup)
cli.add_command(register)


if __name__ == "__main__":
    cli()
