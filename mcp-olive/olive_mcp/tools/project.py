import copy
import uuid
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree
from xml.dom import minidom

from ..ovexml import OveProject, OveNode


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

            for ptr, node in proj.nodes.items():
                name = node.name or "(unnamed)"

                if "sequence" in node.node_id:
                    seq_info = [f"  Sequence: {name} (ptr={ptr})"]
                    vp = node.inputs.get("video_params")
                    w = getattr(vp, 'value', "")
                    h = getattr(vp, 'value', "")
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

        except ElementTree.ParseError as e:
            return f"Failed to parse project XML: {e}"
        except Exception as e:
            return f"Error reading project: {e}"

    def _make_xml_pretty(self, elem: ElementTree.Element) -> str:
        rough = ElementTree.tostring(elem, encoding="unicode")
        reparsed = minidom.parseString(rough.encode())
        return reparsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

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
            tree = ElementTree.parse(str(src))
            root = tree.getroot()
        except Exception as e:
            return f"Failed to parse project: {e}"

        try:
            footage = ElementTree.SubElement(root, "node",
                id="org.olivevideoeditor.Olive.footage",
                name=media.stem)
            ElementTree.SubElement(footage, "uuid").text = str(uuid.uuid4())
            ElementTree.SubElement(footage, "uuid").text = str(uuid.uuid4())
            ElementTree.SubElement(footage, "position", x="0", y="0")
            ElementTree.SubElement(footage, "locked", flags="0")

            filename = ElementTree.SubElement(footage, "input", id="filename")
            ElementTree.SubElement(filename, "standard_value").text = str(media)

            vp = ElementTree.SubElement(footage, "input", id="video_params")
            ElementTree.SubElement(vp, "standard_value",
                width="0", height="0", format="0",
                pixel_aspect_ratio="1", interlacing="0", divider="0",
                frame_rate_numerator="0", frame_rate_denominator="0",
                color_range="0")

            ap = ElementTree.SubElement(footage, "input", id="audio_params")
            ElementTree.SubElement(ap, "standard_value",
                sample_rate="0", channel_layout="0", format="0")

            xml_content = self._make_xml_pretty(root)
            with open(src, "w", encoding="utf-8") as f:
                f.write(xml_content)

            return f"Added footage: {media.name}\n  Project: {src}"

        except Exception as e:
            return f"Error adding clip: {e}"
