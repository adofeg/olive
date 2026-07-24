import json
import shutil
from datetime import datetime
from pathlib import Path


class BackupManager:
    def __init__(self, backup_dir: str | None = None):
        if backup_dir:
            self.backup_root = Path(backup_dir)
        else:
            self.backup_root = Path.home() / ".olive-mcp" / "backups"
        self.backup_root.mkdir(parents=True, exist_ok=True)
        self._index_path = self.backup_root / "index.json"
        self._load_index()

    def _load_index(self):
        if self._index_path.exists():
            with open(self._index_path) as f:
                self._index = json.load(f)
        else:
            self._index = {}

    def _save_index(self):
        with open(self._index_path, "w") as f:
            json.dump(self._index, f, indent=2)

    def _project_key(self, project_path: str) -> str:
        return str(Path(project_path).resolve())

    def create_backup(self, project_path: str) -> str | None:
        src = Path(project_path).resolve()
        if not src.exists():
            return None

        key = self._project_key(project_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_root / key.lstrip("/").replace("/", "_")
        backup_dir.mkdir(parents=True, exist_ok=True)

        ext = src.suffix if src.suffix else ".ovexml"
        backup_path = backup_dir / f"{src.stem}_{timestamp}{ext}"
        shutil.copy2(str(src), str(backup_path))

        if key not in self._index:
            self._index[key] = {"project": key, "backups": []}
        self._index[key]["backups"].append({
            "id": timestamp,
            "path": str(backup_path),
            "timestamp": datetime.now().isoformat(),
        })
        self._save_index()

        return str(backup_path)

    def list_backups(self, project_path: str) -> list[dict]:
        key = self._project_key(project_path)
        if key not in self._index:
            return []
        return list(reversed(self._index[key]["backups"]))

    def get_backup_path(self, project_path: str, backup_id: str) -> str | None:
        key = self._project_key(project_path)
        if key not in self._index:
            return None
        for b in self._index[key]["backups"]:
            if b["id"] == backup_id:
                return b["path"]
        return None

    def restore_backup(self, project_path: str, backup_id: str) -> str:
        backup_path = self.get_backup_path(project_path, backup_id)
        if not backup_path:
            return f"No backup found with ID: {backup_id}"

        src = Path(backup_path)
        dst = Path(project_path).resolve()

        backup_of_original = self.create_backup(project_path)
        status = f"Auto-backup of current project: {backup_of_original}\n" if backup_of_original else ""

        shutil.copy2(str(src), str(dst))
        return f"{status}Restored {backup_path} -> {project_path}"
