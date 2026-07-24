from pathlib import Path
from xml.etree import ElementTree


class PremierePresetImporter:
    def import_epr(self, epr_path: str, output_dir: str | None = None) -> str:
        src = Path(epr_path).resolve()
        if not src.exists():
            return f"File not found: {src}"
        if src.suffix.lower() != ".epr":
            return f"Not a Premiere preset (.epr): {src}"

        tree = ElementTree.parse(str(src))
        root = tree.getroot()

        if root.tag != "PremiereData":
            return f"Not a valid Premiere preset file: {root.tag}"

        name = self._get_text(root, "PresetName") or src.stem
        name = name.split("=")[-1] if "=" in name else name

        exporter_type = self._get_text(root, "ExporterFileType")
        fmt = self._map_exporter_to_format(exporter_type)

        video_codec_val = self._get_param_value(root, "ADBEVideoCodec")
        vcodec = self._map_video_codec(video_codec_val)
        width = self._get_param_value(root, "ADBEVideoWidth") or "1920"
        height = self._get_param_value(root, "ADBEVideoHeight") or "1080"
        fps_raw = self._get_param_value(root, "ADBEVideoFPS")
        fps_num, fps_den = self._parse_fps(fps_raw)
        profile = self._get_param_value(root, "ADBEVideoMPEGProfile") or "0"
        level = self._get_param_value(root, "ADBEVideoMPEGProfileLevel") or "0"
        aspect = self._get_param_value(root, "ADBEVideoAspect") or "1,1"

        audio_codec = self._get_param_aux(root, "ADBEAudioCodec") or "AAC"
        acodec = self._map_audio_codec(audio_codec)
        sample_rate = self._get_param_value(root, "ADBEAudioRatePerSecond") or "48000"
        channels = self._get_param_value(root, "ADBEAudioNumChannels") or "2"
        audio_bitrate = self._get_param_value(root, "ADBEAudioBitrate") or "320"

        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<export version="1">
  <filename/>
  <format>{fmt}</format>
  <video enabled="1">
    <codec>{vcodec}</codec>
    <width>{width}</width>
    <height>{height}</height>
    <pixelaspect>{aspect}</pixelaspect>
    <timebase>
      <numerator>{fps_num}</numerator>
      <denominator>{fps_den}</denominator>
    </timebase>
    <pixfmt>yuv420p</pixfmt>
    <color>
      <output>sRGB</output>
    </color>
    <opts>
      <entry><key>profile</key><value>{self._map_h264_profile(profile)}</value></entry>
      <entry><key>level</key><value>{self._map_h264_level(level)}</value></entry>
      <entry><key>preset</key><value>5</value></entry>
    </opts>
  </video>
  <audio enabled="1">
    <codec>{acodec}</codec>
    <samplerate>{sample_rate}</samplerate>
    <channellayout>{self._map_channels(channels)}</channellayout>
    <bitrate>{audio_bitrate}</bitrate>
  </audio>
</export>'''

        preset_dir = Path(output_dir) if output_dir else self._get_olive_preset_dir()
        preset_dir.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(c for c in name if c.isalnum() or c in " ._-").strip()
        preset_path = preset_dir / f"{safe_name}.xml"
        preset_path.write_text(xml, encoding="utf-8")

        return (
            f"Imported Premiere preset: {src.name}\n"
            f"  Name: {name}\n"
            f"  Format: {fmt}, Codec: {vcodec}\n"
            f"  Resolution: {width}x{height} @ {fps_num}/{fps_den} fps\n"
            f"  Audio: {acodec} {sample_rate}Hz {channels}ch\n"
            f"  Saved: {preset_path}"
        )

    def _get_text(self, root: ElementTree.Element, tag: str) -> str:
        el = root.find(tag)
        return el.text.strip() if el is not None and el.text else ""

    def _get_param_value(self, root: ElementTree.Element, param_id: str) -> str:
        for p in root.findall(f".//ExporterParam[ParamIdentifier='{param_id}']"):
            v = p.find("ParamValue")
            if v is not None and v.text:
                return v.text.strip()
        return ""

    def _get_param_aux(self, root: ElementTree.Element, param_id: str) -> str:
        for p in root.findall(f".//ExporterParam[ParamIdentifier='{param_id}']"):
            v = p.find("ParamAuxValue")
            if v is not None and v.text:
                return v.text.strip()
        return ""

    def _map_exporter_to_format(self, val: str) -> str:
        mapping = {
            "1211250228": "2",
            "1397114178": "3",
            "1397114179": "3",
            "1396918338": "1",
        }
        return mapping.get(val, "2")

    def _map_video_codec(self, val: str) -> str:
        mapping = {
            "0": "0",
            "1735551332": "10",
            "1752589105": "3",
            "1752331877": "5",
            "1819109481": "6",
            "1819110453": "7",
            "1652196449": "11",
        }
        return mapping.get(val, "0")

    def _map_audio_codec(self, name: str) -> str:
        name = name.upper()
        if "AAC" in name:
            return "1"
        if "MP3" in name:
            return "2"
        if "PCM" in name:
            return "0"
        return "1"

    def _map_channels(self, val: str) -> str:
        mapping = {"1": "4", "2": "3", "6": "63", "8": "255"}
        return mapping.get(val, "3")

    def _map_h264_profile(self, val: str) -> str:
        mapping = {"0": "66", "1": "77", "2": "88", "3": "100", "4": "110", "5": "122"}
        return mapping.get(val, "100")

    def _map_h264_level(self, val: str) -> str:
        try:
            n = int(val)
            levels = {0: "1", 9: "1b", 10: "1.1", 11: "1.2", 12: "1.3",
                      20: "2", 21: "2.1", 22: "2.2",
                      30: "3", 31: "3.1", 32: "3.2",
                      40: "4", 41: "4.1", 42: "4.2",
                      50: "5", 51: "5.1", 52: "5.2"}
            return levels.get(n, "4.1")
        except ValueError:
            return "4.1"

    def _parse_fps(self, raw: str | None) -> tuple[str, str]:
        if not raw:
            return "30", "1"
        try:
            val = int(raw)
            mapping = {
                853333333: ("24000", "1001"),
                846720000: ("24000", "1001"),
                8467200000: ("24000", "1001"),
                803584000: ("30000", "1001"),
                8035840000: ("30000", "1001"),
                708750000: ("25", "1"),
                7087500000: ("25", "1"),
                600000000: ("30", "1"),
                6000000000: ("30", "1"),
                478080000: ("50", "1"),
                4780800000: ("50", "1"),
                400000000: ("60", "1"),
                4000000000: ("60", "1"),
            }
            return mapping.get(val, ("30", "1"))
        except (ValueError, TypeError):
            return ("30", "1")

    def _get_olive_preset_dir(self) -> Path:
        import os
        config = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
        return Path(config) / "olivevideoeditor.org" / "Olive" / "exportpresets"


class CubeLutImporter:
    def import_cube(self, cube_path: str) -> str:
        src = Path(cube_path).resolve()
        if not src.exists():
            return f"File not found: {src}"

        lines = src.read_text().splitlines()
        title = ""
        size = 32
        domain_min = [0.0, 0.0, 0.0]
        domain_max = [1.0, 1.0, 1.0]
        data_lines = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                if line.startswith("# ") or line.startswith("#"):
                    t = line.lstrip("#").strip()
                    if t:
                        title = t
                continue
            if line.upper().startswith("TITLE"):
                parts = line.split("\"")
                if len(parts) >= 2:
                    title = parts[1]
                continue
            if line.upper().startswith("LUT_3D_SIZE"):
                parts = line.split()
                if len(parts) >= 2:
                    size = int(parts[1])
                continue
            if line.upper().startswith("DOMAIN_MIN"):
                parts = line.split()
                if len(parts) >= 4:
                    domain_min = [float(parts[1]), float(parts[2]), float(parts[3])]
                continue
            if line.upper().startswith("DOMAIN_MAX"):
                parts = line.split()
                if len(parts) >= 4:
                    domain_max = [float(parts[1]), float(parts[2]), float(parts[3])]
                continue
            data_lines.append(line)

        data_count = len(data_lines)
        expected = size ** 3

        title = title or src.stem

        return (
            f"LUT info: {src.name}\n"
            f"  Title: {title}\n"
            f"  Size: {size}x{size}x{size} ({expected} entries, found {data_count})\n"
            f"  Domain: R=[{domain_min[0]},{domain_max[0]}] "
            f"G=[{domain_min[1]},{domain_max[1]}] "
            f"B=[{domain_min[2]},{domain_max[2]}]\n"
            f"\n"
            f"Olive uses OpenColorIO (OCIO) for LUT management. To use this LUT:\n"
            f"  1. Copy {src.name} to your OCIO config's luts/ directory\n"
            f"  2. Add a FileTransform in your config.ocio referencing it\n"
            f"  3. Or use the MCP: olive_create_lut_node (coming soon)\n"
            f"\n"
            f"OCIO supports .cube natively - your LUT will work if referenced\n"
            f"from a custom OCIO configuration."
        )
