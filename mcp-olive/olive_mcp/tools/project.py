from datetime import datetime
from pathlib import Path

from ..ovexml import OveProject


class ProjectTool:
    def get_info(self, project_path: str) -> str:
        src = Path(project_path).resolve()
        if not src.exists():
            return f"Project file not found: {src}"

        try:
            proj = OveProject()
            proj.load(str(src))

            lines = [f"Project: {src.name}", f"Path: {src}", ""]

            sequences = []
            footage_list = []
            clips = []
            tracks = []
            effects = []
            resolution_map: dict[int, str] = {}

            try:
                raw_tree = __import__("xml.etree.ElementTree", fromlist=["ElementTree"]).ElementTree.parse(str(src))
                for raw_node in raw_tree.findall(".//node"):
                    rptr = int(raw_node.get("ptr", "0"))
                    for inp in raw_node.findall("input"):
                        if inp.get("id") == "video_params":
                            for sv in inp.iter("standard_value"):
                                w = sv.get("width", "?")
                                h = sv.get("height", "?")
                                resolution_map[rptr] = f"{w}x{h}"
            except Exception:
                pass

            for ptr, node in proj.nodes.items():
                name = node.name or "(unnamed)"

                if "sequence" in node.node_id:
                    res = resolution_map.get(ptr, "?x?")
                    seq_info = [f"  Sequence: {name} (ptr={ptr})"]
                    if res != "?x?":
                        seq_info.append(f"    Resolution: {res}")
                    for c in node.connections:
                        if c.input_id == "tex_in":
                            target = proj.get_node(c.target_ptr)
                            if target:
                                seq_info.append(f"    Track: {target.name or 'unnamed'} (ptr={target.ptr})")
                    sequences.append("\n".join(seq_info))

                elif "footage" in node.node_id:
                    fn = ""
                    fn_inp = node.inputs.get("filename")
                    if fn_inp:
                        fn = fn_inp.value
                    footage_list.append(f"  Footage: {name} (ptr={ptr}) file={fn}")

                elif "clip" in node.node_id:
                    length = node.inputs.get("length_in")
                    lv = length.value if length else "?"
                    media_in = node.inputs.get("media_in_in")
                    mv = media_in.value if media_in else "0/1"
                    speed = node.inputs.get("speed_in")
                    sv = speed.value if speed else "1"
                    clips.append(f"  Clip: {name} (ptr={ptr}) length={lv} media_in={mv} speed={sv}")

                elif "track" in node.node_id:
                    tracks.append(f"  Track: {name or 'unnamed'} (ptr={ptr})")

                elif "opacity" in node.node_id or "colorize" in node.node_id:
                    effects.append(f"  Effect: {node.node_id.split('.')[-1]} (ptr={ptr})")

            lines.append(f"Sequences ({len(sequences)}):")
            lines.extend(sequences if sequences else ["  (none)"])
            lines.append("")
            lines.append(f"Tracks ({len(tracks)}):")
            lines.extend(tracks if tracks else ["  (none)"])
            lines.append("")
            lines.append(f"Clips ({len(clips)}):")
            lines.extend(clips if clips else ["  (none)"])
            lines.append("")
            lines.append(f"Footage ({len(footage_list)}):")
            lines.extend(footage_list if footage_list else ["  (none)"])
            lines.append("")
            lines.append(f"Effects ({len(effects)}):")
            lines.extend(effects if effects else ["  (none)"])
            lines.append("")
            lines.append(f"Total nodes: {len(proj.nodes)}")

            return "\n".join(lines)

        except Exception as e:
            return f"Error reading project: {e}"

    def create_project(
        self,
        output_path: str,
        width: int = 1920,
        height: int = 1080,
        fps_numerator: int = 30,
        fps_denominator: int = 1,
        sequence_name: str = "Sequence 1",
        media_files: list[str] | None = None,
    ) -> str:
        width = max(16, min(width, 7680))
        height = max(16, min(height, 4320))
        fps_numerator = max(1, fps_numerator)
        fps_denominator = max(1, fps_denominator)
        if fps_numerator > 240:
            fps_numerator = 240

        dst = Path(output_path).resolve()
        dst.parent.mkdir(parents=True, exist_ok=True)

        proj = OveProject()
        seq = proj.make_sequence(sequence_name, width, height, fps_numerator, fps_denominator)
        track = proj.make_track("V1")
        seq.connect("tex_in", track.ptr, element=0)
        tex_arr = seq.inputs.get("tex_in")
        if tex_arr and hasattr(tex_arr, 'count'):
            tex_arr.count = 1

        log = []
        if media_files:
            for i, mf in enumerate(media_files):
                mp = Path(mf)
                if mp.exists():
                    footage = proj.make_footage(str(mp.resolve()))
                    clip = proj.make_clip(mp.stem, "300/1", footage.ptr)
                    gap = proj.make_gap("300/1")
                    track.inputs["block_in"].count = (i * 2) + 2
                    track.connect("block_in", gap.ptr, element=i * 2)
                    track.connect("block_in", clip.ptr, element=i * 2 + 1)
                    log.append(f"  Added clip: {mp.name} (ptr={clip.ptr})")

        proj.save(str(dst))
        lines = [f"Project created: {dst}",
                 f"  Resolution: {width}x{height}",
                 f"  FPS: {fps_numerator}/{fps_denominator}",
                 f"  Sequence: {sequence_name}"]
        lines.extend(log)
        return "\n".join(lines)

    def add_clip(
        self,
        project_path: str,
        media_path: str,
        sequence_name: str | None = None,
        track_index: int = 0,
    ) -> str:
        src = Path(project_path).resolve()
        media = Path(media_path).resolve()

        if not src.exists():
            return f"Project not found: {src}"
        if not media.exists():
            return f"Media not found: {media}"

        try:
            proj = OveProject()
            proj.load(str(src))
            footage = proj.make_footage(str(media))
            seq_ptr = self._find_sequence(proj)
            if seq_ptr is not None:
                from .editor import EditorTool
                et = EditorTool()
                clip = proj.make_clip(media.stem, "300/1", footage.ptr)
                et._attach_clip_to_track(proj, seq_ptr, clip, track_index)
            proj.save(str(src))
            return f"Added footage: {media.name} (ptr={footage.ptr})\n  Project: {src}"
        except Exception as e:
            return f"Error adding clip: {e}"

    def _find_sequence(self, proj: OveProject) -> int | None:
        for ptr, n in proj.nodes.items():
            if "sequence" in n.node_id:
                return ptr
        return None
