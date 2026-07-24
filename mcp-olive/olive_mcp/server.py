from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .tools.backup import BackupManager
from .tools.export import ExportTool
from .tools.project import ProjectTool
from .tools.editor import EditorTool

app = FastMCP("olive-mcp", instructions="Edit and export Olive video editor projects from CLI. Always creates backups before modifications.")
backup_mgr = BackupManager()
export_tool = ExportTool()
project_tool = ProjectTool()
editor_tool = EditorTool()


@app.tool(description="Export a sequence from an Olive project to a video file. Creates backup first.")
def olive_export(project_path: str, output_path: str, sequence_name: str = "") -> str:
    """Export an Olive project sequence to video. Backup is created automatically."""
    src = Path(project_path).resolve()
    dst = Path(output_path).resolve()
    backup_mgr.create_backup(str(src))
    return export_tool.export(str(src), str(dst), sequence_name or None)


@app.tool(description="Create a timestamped backup copy of an Olive project file.")
def olive_backup_create(project_path: str) -> str:
    """Create a backup of the project file. Stored in ~/.olive-mcp/backups/."""
    path = backup_mgr.create_backup(str(Path(project_path).resolve()))
    return f"Backup created: {path}" if path else f"Failed to create backup for {project_path}"


@app.tool(description="List all available backups for a given Olive project.")
def olive_backup_list(project_path: str) -> str:
    """List all backups for a project with IDs and timestamps."""
    backups = backup_mgr.list_backups(str(Path(project_path).resolve()))
    if not backups:
        return "No backups found"
    lines = ["Available backups:"]
    for b in backups:
        lines.append(f"  {b['id']}: {b['path']} ({b['timestamp']})")
    return "\n".join(lines)


@app.tool(description="Restore a project from a specific backup by ID. Creates backup of current state first.")
def olive_backup_restore(project_path: str, backup_id: str) -> str:
    """Restore a previous backup. The current state is backed up automatically first."""
    return backup_mgr.restore_backup(str(Path(project_path).resolve()), backup_id)


@app.tool(description="Get detailed info about an Olive project: sequences, resolution, footage, node count.")
def olive_project_info(project_path: str) -> str:
    """Show sequences, footage files, resolution, and node count from a .ove/.ovexml file."""
    return project_tool.get_info(str(Path(project_path).resolve()))


@app.tool(description="Create a new Olive project with one sequence at specified resolution and FPS.")
def olive_create_project(
    output_path: str,
    width: int = 1920,
    height: int = 1080,
    fps_numerator: int = 30,
    fps_denominator: int = 1,
    sequence_name: str = "Sequence 1",
) -> str:
    """Create an empty Olive project with one sequence. Resolution and FPS are configurable."""
    return project_tool.create_project(
        str(Path(output_path).resolve()),
        width=width,
        height=height,
        fps_numerator=fps_numerator,
        fps_denominator=fps_denominator,
        sequence_name=sequence_name,
    )


@app.tool(description="Add a media file (video/audio/image) as footage to an Olive project. Backup is created first.")
def olive_add_clip(project_path: str, media_path: str) -> str:
    """Import media into project as footage node. Backup created before modification."""
    src = Path(project_path).resolve()
    media = Path(media_path).resolve()
    backup_mgr.create_backup(str(src))
    return project_tool.add_clip(str(src), str(media))


@app.tool(description="Edit a video project with natural language instructions. Can add clips, effects, transitions, create timelines, etc.")
def olive_edit(project_path: str, instructions: str) -> str:
    """Edit an Olive project using natural language instructions.

    Supported operations:
    - Add clips to timeline: 'add clip video.mp4 at 0s duration 10s on track 1'
    - Apply effects: 'apply colorize with color red saturation 70% to clip 1'
    - Add transitions: 'add cross dissolve 1s between clip 1 and clip 2'
    - Change speed: 'set clip 1 speed to 2x'
    - Trim clips: 'trim clip 1 to start at 5s end at 15s'
    - Export: 'export to output.mp4'

    Creates a backup before any modification.
    """
    src = Path(project_path).resolve()
    backup_mgr.create_backup(str(src))
    return editor_tool.edit(str(src), instructions)


@app.tool(description="Directly edit an Olive project XML. Low-level tool for precise control.")
def olive_edit_xml(project_path: str, operations: str) -> str:
    """Apply low-level XML operations to an Olive project.

    Format each operation on a new line:
      add_footage /path/to/media.mp4
      add_clip footage_ptr=1 length=300/1 track=0
      add_effect clip_ptr=2 type=opacity params=val_in:0.5
      add_transition clip_a=2 clip_b=3 type=crossdissolve length=30/1
      set_input node_ptr=2 input=speed_in value=2
      export output.mp4
    """
    src = Path(project_path).resolve()
    backup_mgr.create_backup(str(src))
    return editor_tool.edit_xml(str(src), operations)


@app.tool(description="Restore a project from a backup file path to its original location.")
def olive_backup_copy(backup_path: str, original_path: str) -> str:
    """Copy a backup file to its original project location."""
    import shutil
    shutil.copy2(str(Path(backup_path).resolve()), str(Path(original_path).resolve()))
    return f"Restored {backup_path} -> {original_path}"


def main():
    app.run(transport="stdio")


if __name__ == "__main__":
    main()
