import uuid
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree
from xml.dom import minidom


class ProjectTool:
    def get_info(self, project_path: str) -> str:
        src = Path(project_path).resolve()
        if not src.exists():
            return f"Project file not found: {src}"

        try:
            tree = ElementTree.parse(str(src))
            root = tree.getroot()

            lines = [f"Project: {src.name}", f"Path: {src}", ""]

            sequences = []
            footage_list = []
            for node in root.findall(".//node"):
                node_id = node.get("id", "")
                name = node.get("name", "(unnamed)")

                if "sequence" in node_id or "Sequence" in name:
                    seq_info = [f"  Sequence: {name}"]
                    video_params = node.find(".//input[@id='video_params']")
                    if video_params is not None:
                        for sv in video_params.findall("standard_value"):
                            w = sv.get("width", "?")
                            h = sv.get("height", "?")
                            seq_info.append(f"    Resolution: {w}x{h}")
                            break
                    sequences.append("\n".join(seq_info))

                elif "footage" in node_id or "Footage" in node_id:
                    filename = ""
                    for child in node.iter():
                        if child.text and ("/" in child.text or "\\" in child.text):
                            filename = child.text
                            break
                    footage_list.append(f"  Footage: {name} ({filename})")

            lines.append(f"Sequences ({len(sequences)}):")
            lines.extend(sequences if sequences else ["  (none)"])

            lines.append("")
            lines.append(f"Footage ({len(footage_list)}):")
            lines.extend(footage_list if footage_list else ["  (none)"])

            lines.append("")
            lines.append(f"Total nodes: {len(root.findall('.//node'))}")

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
    ) -> str:
        dst = Path(output_path).resolve()
        dst.parent.mkdir(parents=True, exist_ok=True)

        root = ElementTree.Element("project", version="230220")

        project_uuid = str(uuid.uuid4())
        ElementTree.SubElement(root, "uuid").text = project_uuid
        ElementTree.SubElement(root, "name").text = dst.stem
        ElementTree.SubElement(root, "color_config", filename="")
        ElementTree.SubElement(root, "color_reference_space").text = "aces 1.0 sdr video"

        folder = ElementTree.SubElement(root, "node", id="org.olivevideoeditor.Olive.folder", name="Root")
        ElementTree.SubElement(folder, "uuid").text = str(uuid.uuid4())
        ElementTree.SubElement(folder, "uuid").text = str(uuid.uuid4())
        ElementTree.SubElement(folder, "position", x="0", y="0")
        ElementTree.SubElement(folder, "locked", flags="0")

        seq_uuid = str(uuid.uuid4())
        seq = ElementTree.SubElement(root, "node", id="org.olivevideoeditor.Olive.sequence", name=sequence_name)
        ElementTree.SubElement(seq, "uuid").text = seq_uuid
        ElementTree.SubElement(seq, "uuid").text = str(uuid.uuid4())
        ElementTree.SubElement(seq, "position", x="0", y="0")
        ElementTree.SubElement(seq, "locked", flags="0")

        vp = ElementTree.SubElement(seq, "input", id="video_params")
        sv = ElementTree.SubElement(vp, "standard_value")
        sv.set("width", str(width))
        sv.set("height", str(height))
        sv.set("format", "0")
        sv.set("pixel_aspect_ratio", "1")
        sv.set("interlacing", "0")
        sv.set("divider", "0")
        sv.set("frame_rate_numerator", str(fps_numerator))
        sv.set("frame_rate_denominator", str(fps_denominator))
        sv.set("color_range", "0")

        ap = ElementTree.SubElement(seq, "input", id="audio_params")
        sv2 = ElementTree.SubElement(ap, "standard_value")
        sv2.set("sample_rate", "48000")
        sv2.set("channel_layout", "3")
        sv2.set("format", "1")

        xml_content = self._make_xml_pretty(root)
        with open(dst, "w", encoding="utf-8") as f:
            f.write(xml_content)

        return f"Project created: {dst}\n  Resolution: {width}x{height}\n  FPS: {fps_numerator}/{fps_denominator}\n  Sequence: {sequence_name}"

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
