"""Pipeline CLI commands.

Each module exports a Click command and the underlying library
function (run_* / create_*) for programmatic use.
"""

from pipeline.commands.artist_studio import artist_studio
from pipeline.commands.avatar import avatar
from pipeline.commands.create_artist import create_artist
from pipeline.commands.curate import curate
from pipeline.commands.frame import analyze_frames, frame
from pipeline.commands.full import full
from pipeline.commands.generate import generate
from pipeline.commands.mockup import mockup
from pipeline.commands.process_images import process_images
from pipeline.commands.register import register
from pipeline.commands.room_mockup import room_mockup
from pipeline.commands.room_templates_cmd import room_templates_group
from pipeline.commands.standardise import standardise
from pipeline.commands.upscale import upscale

__all__ = [
    "artist_studio",
    "avatar",
    "create_artist",
    "curate",
    "analyze_frames",
    "frame",
    "full",
    "generate",
    "mockup",
    "process_images",
    "register",
    "room_mockup",
    "room_templates_group",
    "standardise",
    "upscale",
]
