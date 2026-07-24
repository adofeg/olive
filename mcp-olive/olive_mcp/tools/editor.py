import re
import shutil
import tempfile
from pathlib import Path

from ..ovexml import OveProject


class EditorTool:
    def __init__(self):
        self._ptr_counter = 0
        self._footage_map: dict[str, int] = {}

    def _next_ptr(self) -> int:
        self._ptr_counter += 1
        return self._ptr_counter

    def edit(self, project_path: str, instructions: str) -> str:
        lines = ["=== Olive Edit ==="]
        proj = OveProject()
        proj.load(project_path)
        log = []

        instructions_lower = instructions.lower()

        if "add clip" in instructions_lower or "add footage" in instructions_lower:
            self._handle_add_clip(proj, instructions, log)
        if "transition" in instructions_lower or "cross dissolve" in instructions_lower or "dip" in instructions_lower:
            self._handle_transition(proj, instructions, log)
        if "colorize" in instructions_lower or "effect" in instructions_lower:
            self._handle_effect(proj, instructions, log)
        if "speed" in instructions_lower:
            self._handle_speed(proj, instructions, log)
        if "export" in instructions_lower:
            self._handle_export(proj, instructions, log, project_path)

        if not log:
            log.append("No recognized instructions found. Try: add clip, transition, effect, speed, export")

        proj.save(project_path)
        lines.extend(log)
        lines.append(f"Project saved: {project_path}")
        return "\n".join(lines)

    def edit_xml(self, project_path: str, operations: str) -> str:
        proj = OveProject()
        proj.load(project_path)
        log = []

        for line in operations.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            cmd = parts[0]
            args = parts[1:]

            if cmd == "add_footage" and args:
                fp = args[0]
                node = proj.make_footage(fp)
                log.append(f"  Added footage '{fp}' (ptr={node.ptr})")

            elif cmd == "add_clip" and args:
                params = self._parse_kv(args)
                footage_ptr = int(params.get("footage_ptr", "0"))
                length = params.get("length", "300/1")
                track_idx = int(params.get("track", "0"))
                if not proj.get_node(footage_ptr):
                    log.append(f"  ERROR: footage ptr {footage_ptr} not found")
                    continue
                clip = proj.make_clip("Clip", length, footage_ptr)
                seq_ptr = self._find_sequence(proj)
                if seq_ptr:
                    self._attach_clip_to_track(proj, seq_ptr, clip, track_idx)
                log.append(f"  Added clip (ptr={clip.ptr}) length={length} on track {track_idx}")

            elif cmd == "add_effect" and args:
                params = self._parse_kv(args)
                clip_ptr = int(params.get("clip_ptr", "0"))
                etype = params.get("type", "opacity")
                raw_params = {}
                if "params" in params:
                    for p in params["params"].split(","):
                        if ":" in p:
                            k, v = p.split(":", 1)
                            raw_params[k.strip()] = v.strip()
                if proj.get_node(clip_ptr):
                    effect = proj.make_effect(etype, clip_ptr, raw_params)
                    log.append(f"  Added {etype} effect (ptr={effect.ptr}) to clip {clip_ptr}")

            elif cmd == "add_transition" and args:
                params = self._parse_kv(args)
                clip_a = int(params.get("clip_a", "0"))
                clip_b = int(params.get("clip_b", "0"))
                ttype = params.get("type", "crossdissolve")
                length = params.get("length", "30/1")
                if proj.get_node(clip_a) and proj.get_node(clip_b):
                    trans = proj.make_transition(ttype, length, clip_a, clip_b)
                    log.append(f"  Added {ttype} transition (ptr={trans.ptr}) between clip {clip_a} and {clip_b}")
                else:
                    log.append(f"  ERROR: clip ptrs {clip_a}/{clip_b} not found")

            elif cmd == "set_input" and args:
                params = self._parse_kv(args)
                nptr = int(params.get("node_ptr", "0"))
                inp_id = params.get("input", "")
                value = params.get("value", "")
                node = proj.get_node(nptr)
                if node and inp_id:
                    node.inputs[inp_id] = node.add_input(inp_id, value)
                    log.append(f"  Set {inp_id}={value} on node {nptr}")

            elif cmd == "export" and args:
                dst = args[0]
                from ..tools.export import ExportTool
                et = ExportTool()
                result = et.export(project_path, dst)
                log.append(f"  Export: {result}")

        proj.save(project_path)
        log.append(f"Project saved: {project_path}")
        return "\n".join(log)

    def _parse_kv(self, args: list[str]) -> dict[str, str]:
        params = {}
        for a in args:
            if "=" in a:
                k, v = a.split("=", 1)
                params[k] = v
        return params

    def _find_sequence(self, proj: OveProject) -> int | None:
        for ptr, node in proj.nodes.items():
            if "sequence" in node.node_id:
                return ptr
        return None

    def _ensure_track(self, proj: OveProject, seq_ptr: int, track_idx: int) -> int | None:
        seq = proj.get_node(seq_ptr)
        if not seq:
            return None
        for conn in seq.connections:
            if conn.input_id == "tex_in" and conn.element == track_idx:
                existing = proj.get_node(conn.target_ptr)
                if existing:
                    return existing.ptr
        track = proj.make_track(f"V{track_idx + 1}")
        seq.connect("tex_in", track.ptr, element=track_idx)
        tex_arr = seq.inputs.get("tex_in")
        if tex_arr and hasattr(tex_arr, 'count'):
            tex_arr.count = max(tex_arr.count, track_idx + 1)
        return track.ptr

    def _attach_clip_to_track(self, proj: OveProject, seq_ptr: int, clip, track_idx: int):
        track_ptr = self._ensure_track(proj, seq_ptr, track_idx)
        if not track_ptr:
            return
        track = proj.get_node(track_ptr)
        if not track:
            return
        gap = proj.make_gap(clip.inputs["length_in"].value)
        current_count = track.inputs["block_in"].count
        track.inputs["block_in"].count = current_count + 2
        track.connect("block_in", gap.ptr, element=current_count)
        track.connect("block_in", clip.ptr, element=current_count + 1)

    def _handle_add_clip(self, proj: OveProject, instructions: str, log: list):
        for m in re.finditer(r'(?:add|place|put)\s+(?:clip|footage|file|video)\s+["\']?([^"\'\s]+\.\w+)["\']?', instructions, re.IGNORECASE):
            media_path = m.group(1)
            if not Path(media_path).exists():
                log.append(f"  WARNING: Media not found: {media_path}")
                continue
            footage = proj.make_footage(media_path)
            log.append(f"  Added footage: {media_path} (ptr={footage.ptr})")

            length_match = re.search(r'(?:duration|length)\s+(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)?', instructions, re.IGNORECASE)
            length = f"{int(float(length_match.group(1)))}/1" if length_match else "300/1"
            clip = proj.make_clip(Path(media_path).stem, length, footage.ptr)
            log.append(f"  Added clip '{clip.name}' length={length} (ptr={clip.ptr})")

            seq_ptr = self._find_sequence(proj)
            if seq_ptr:
                track_m = re.search(r'track\s+(\d+)', instructions, re.IGNORECASE)
                ti = int(track_m.group(1)) - 1 if track_m else 0
                self._attach_clip_to_track(proj, seq_ptr, clip, ti)
                log.append(f"  Placed on track {ti + 1}")

    def _handle_transition(self, proj: OveProject, instructions: str, log: list):
        dur_m = re.search(r'(?:duration|length)\s+(\d+(?:\.\d+)?)\s*(?:s|sec|seconds|frames?)?', instructions, re.IGNORECASE)
        length = dur_m.group(1) if dur_m else "30"
        if "/" not in length:
            length = f"{length}/1"
        trans_type = "crossdissolve"
        if "dip to color" in instructions.lower() or "diptocolor" in instructions.lower():
            trans_type = "diptocolor"
        clips = [n for n in proj.nodes.values() if n.node_id == "org.olivevideoeditor.Olive.clip"]
        if len(clips) >= 2:
            t = proj.make_transition(trans_type, length, clips[0].ptr, clips[1].ptr)
            log.append(f"  Added {trans_type} transition length={length} between clips {clips[0].ptr} and {clips[1].ptr}")

    def _handle_effect(self, proj: OveProject, instructions: str, log: list):
        etype = "colorize" if "colorize" in instructions.lower() else "opacity"
        params = {}
        if etype == "colorize":
            sat_m = re.search(r'saturation\s+(\d+)%?', instructions, re.IGNORECASE)
            if sat_m:
                params["saturation_in"] = str(int(sat_m.group(1)) / 100)
            str_m = re.search(r'strength\s+(\d+)%?', instructions, re.IGNORECASE)
            if str_m:
                params["strength_in"] = str(int(str_m.group(1)) / 100)
        else:
            val_m = re.search(r'opacity\s+(\d+)%?', instructions, re.IGNORECASE)
            if val_m:
                params["val_in"] = str(int(val_m.group(1)) / 100)
        clips = [n for n in proj.nodes.values() if n.node_id == "org.olivevideoeditor.Olive.clip"]
        clip_idx = None
        idx_m = re.search(r'(?:to|on)\s+clip\s+(\d+)', instructions, re.IGNORECASE)
        if idx_m:
            clip_idx = int(idx_m.group(1)) - 1
        if clip_idx is not None and clip_idx < len(clips):
            effect = proj.make_effect(etype, clips[clip_idx].ptr, params)
            log.append(f"  Added {etype} effect (ptr={effect.ptr}) to clip {clip_idx + 1}")
        elif clips:
            effect = proj.make_effect(etype, clips[0].ptr, params)
            log.append(f"  Added {etype} effect (ptr={effect.ptr}) to clip 1")

    def _handle_speed(self, proj: OveProject, instructions: str, log: list):
        sp_m = re.search(r'speed\s+(?:to\s+)?(\d+(?:\.\d+)?)\s*x?', instructions, re.IGNORECASE)
        if sp_m:
            speed = sp_m.group(1)
            clips = [n for n in proj.nodes.values() if n.node_id == "org.olivevideoeditor.Olive.clip"]
            if clips:
                clips[0].inputs["speed_in"].value = speed
                log.append(f"  Set clip speed to {speed}x")

    def _handle_export(self, proj: OveProject, instructions: str, log: list, project_path: str = ""):
        exp_m = re.search(r'export\s+(?:to\s+)?["\']?([^"\'\s]+\.\w+)["\']?', instructions, re.IGNORECASE)
        if exp_m:
            dst = exp_m.group(1)
            from ..tools.export import ExportTool
            et = ExportTool()
            result = et.export(project_path, dst)
            log.append(f"  Export: {result}")

    def _handle_create_sequence(self, proj: OveProject, instructions: str, log: list):
        pass
