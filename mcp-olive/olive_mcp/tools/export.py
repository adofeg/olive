import subprocess
import tempfile
from pathlib import Path
from xml.etree import ElementTree


class ExportTool:
    def __init__(self, olive_binary: str | None = None):
        self.olive_binary = olive_binary or self._find_olive()

    def _find_olive(self) -> str:
        candidates = [
            "olive-editor",
            "olive",
            "/usr/local/bin/olive-editor",
            "/usr/bin/olive-editor",
        ]
        for c in candidates:
            try:
                subprocess.run([c, "--version"], capture_output=True, timeout=5)
                return c
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return "olive-editor"

    def export(
        self,
        project_path: str,
        output_path: str,
        sequence_name: str | None = None,
    ) -> str:
        src = Path(project_path).resolve()
        dst = Path(output_path).resolve()

        if not src.exists():
            return f"Project file not found: {src}"

        dst.parent.mkdir(parents=True, exist_ok=True)

        project_xml, needs_cleanup = self._ensure_uncompressed(str(src))
        try:
            if project_xml and sequence_name:
                self._set_active_sequence(project_xml, sequence_name)
        finally:
            if needs_cleanup and project_xml:
                Path(project_xml).unlink(missing_ok=True)

        cmd = [
            self.olive_binary,
            "--headless",
            "--start", str(src),
            "--export", str(dst),
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,
            )
            output = result.stdout + result.stderr
            if result.returncode == 0:
                return f"Export successful: {dst}\n{output}"
            return f"Export failed (code {result.returncode}):\n{output}"
        except FileNotFoundError:
            return (
                f"Olive binary not found at '{self.olive_binary}'.\n"
                "Install Olive or set the OLIVE_BINARY env var.\n"
                f"To build: cd {Path(project_path).parent} && mkdir -p build && cd build && cmake .. && make -j$(nproc)"
            )
        except subprocess.TimeoutExpired:
            return "Export timed out (1 hour limit)"
        except Exception as e:
            return f"Export error: {e}"

    def _ensure_uncompressed(self, project_path: str):
        src = Path(project_path)
        if src.suffix == ".ovexml":
            return str(src), False
        if src.suffix == ".ove":
            try:
                with open(src, "rb") as f:
                    magic = f.read(4)
                    f.seek(0)
                    if magic == b"OVEC":
                        import zlib
                        compressed = f.read()
                        data = zlib.decompress(compressed[4:])
                        import tempfile
                        tmp = tempfile.NamedTemporaryFile(suffix=".ovexml", delete=False)
                        tmp.write(data)
                        tmp.close()
                        return tmp.name, True
            except Exception:
                pass
        return None, False

    def _set_active_sequence(self, project_path: str, sequence_name: str):
        try:
            tree = ElementTree.parse(project_path)
            root = tree.getroot()
            for node in root.findall(".//node"):
                name = node.get("name", "")
                if name == sequence_name or node.get("id", "").endswith("sequence"):
                    for child in node.findall("input"):
                        if child.get("id") == "active":
                            val = child.find("standard_value")
                            if val is not None:
                                val.text = "1"
            tree.write(project_path, xml_declaration=True)
        except Exception:
            pass
