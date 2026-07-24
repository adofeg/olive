import re
from pathlib import Path

from ..ovexml import OveProject


_PATTERNS = {
    "clips": re.compile(
        r'(?:add|place|put|import)\s+(?:clip|footage|file|video|media)\s+'
        r'["\']?([^"\'\s]+\.\w+)["\']?',
        re.IGNORECASE
    ),
    "trim_start": re.compile(
        r'(?:trim|cut|set)\s+(?:clip\s+)?(\d+)\s+(?:start|in|from)\s+(?:at\s+)?'
        r'(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)?',
        re.IGNORECASE
    ),
    "trim_end": re.compile(
        r'(?:trim|cut|set)\s+(?:clip\s+)?(\d+)\s+(?:end|out|to)\s+(?:at\s+)?'
        r'(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)?',
        re.IGNORECASE
    ),
    "duration": re.compile(
        r'(?:duration|length)\s+(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)?',
        re.IGNORECASE
    ),
    "fps": re.compile(
        r'(\d+)\s*(?:fps|f.p.s|frames\s*per\s*second)',
        re.IGNORECASE
    ),
    "track": re.compile(
        r'(?:track|layer)\s+(\d+)',
        re.IGNORECASE
    ),
    "speed": re.compile(
        r'speed\s+(?:to\s+)?(\d+(?:\.\d+)?)\s*x?',
        re.IGNORECASE
    ),
    "transition": re.compile(
        r'(?:add|insert)\s+(.+?)\s+(?:transition|dissolve|wipe)\s+'
        r'(?:duration|length)\s+(\d+(?:\.\d+)?)\s*(?:s|sec|seconds|frames?)?\s*'
        r'(?:between|betw)\s+(?:clip\s+)?(\d+)\s+(?:and|&)\s+(?:clip\s+)?(\d+)',
        re.IGNORECASE
    ),
    "transition_simple": re.compile(
        r'(?:cross\s*dissolve|transition|dip)\s+(?:to\s+color\s+)?'
        r'(\d+(?:\.\d+)?)\s*(?:s|sec|seconds|frames?)?',
        re.IGNORECASE
    ),
    "effect": re.compile(
        r'(?:apply|add|set)\s+(.+?)\s+(?:effect|filter)\s+'
        r'(?:to|on)\s+(?:clip\s+)?(\d+)',
        re.IGNORECASE
    ),
    "effect_simple": re.compile(
        r'(?:apply|add|set)\s+(.+?)\s+(?:to|on)\s+(?:clip\s+)?(\d+)',
        re.IGNORECASE
    ),
    "parameter": re.compile(
        r'(\w+)\s+(\d+(?:\.\d+)?)%?',
        re.IGNORECASE
    ),
    "export": re.compile(
        r'export\s+(?:to\s+)?["\']?([^"\'\s]+\.\w+)["\']?',
        re.IGNORECASE
    ),
    "resolution": re.compile(
        r'(\d+)x(\d+)\s*(?:px|pixels?)?',
        re.IGNORECASE
    ),
    "format": re.compile(
        r'(?:format|container|as)\s+(mp4|mov|mkv|avi|webm|gif)',
        re.IGNORECASE
    ),
}


class EditorTool:
    def __init__(self):
        self._footage_counter = 0

    def _next_label(self) -> str:
        self._footage_counter += 1
        return f"clip_{self._footage_counter}"

    _PARAM_ALIASES = {
        "saturation": "saturation_in",
        "sat": "saturation_in",
        "strength": "strength_in",
        "str": "strength_in",
        "opacity": "val_in",
        "alpha": "val_in",
        "color": "color_in",
        "colour": "color_in",
        "hue": "hue_in",
        "lightness": "lightness_in",
        "luminosity": "preserve_luminosity_in",
        "blur": "radius_in",
        "radius": "radius_in",
    }

    _NON_PARAM_WORDS = {
        "duration", "length", "track", "layer", "clip", "fps",
        "to", "on", "at", "in", "from", "between", "and", "with",
        "add", "apply", "set", "export", "trim", "cut", "speed",
    }

    def _extract_params(self, text: str) -> dict[str, str]:
        params = {}
        for m in _PATTERNS["parameter"].finditer(text):
            key = m.group(1).lower()
            if key in self._NON_PARAM_WORDS:
                continue
            raw_val = m.group(2)
            alias = self._PARAM_ALIASES.get(key, key + "_in")
            val = float(raw_val)
            pct = "%" in m.group(0)
            params[alias] = str(val / 100.0) if pct else str(val)
        return params

    def _find_clips(self, proj: OveProject) -> list[tuple[int, str]]:
        return [
            (ptr, n.name or f"clip_{i}")
            for i, (ptr, n) in enumerate(proj.nodes.items())
            if n.node_id == "org.olivevideoeditor.Olive.clip"
        ]

    def edit(self, project_path: str, instructions: str) -> str:
        proj = OveProject()
        proj.load(project_path)
        log = []
        instr_lower = instructions.lower()

        # 1. ADD CLIPS
        for m in _PATTERNS["clips"].finditer(instructions):
            media_path = m.group(1)
            if not Path(media_path).exists():
                log.append(f"  WARNING: Media not found: {media_path}")
                continue
            dur_m = _PATTERNS["duration"].search(instructions)
            length = f"{int(float(dur_m.group(1)))}/1" if dur_m else "300/1"
            track_m = _PATTERNS["track"].search(instructions)
            track_idx = int(track_m.group(1)) - 1 if track_m else 0

            footage = proj.make_footage(media_path)
            clip = proj.make_clip(Path(media_path).stem, length, footage.ptr)
            seq_ptr = self._find_sequence(proj)
            if seq_ptr:
                self._attach_clip_to_track(proj, seq_ptr, clip, track_idx)
            log.append(f"  Added clip '{clip.name}' (ptr={clip.ptr}) length={length} track={track_idx + 1}")

        # 2. TRIM CLIPS
        all_clips = self._find_clips(proj)
        for m in _PATTERNS["trim_start"].finditer(instructions):
            idx = int(m.group(1)) - 1
            if idx < len(all_clips):
                ptr, _ = all_clips[idx]
                secs = float(m.group(2))
                in_val = f"{int(secs)}/1"
                proj.nodes[ptr].inputs["media_in_in"].value = in_val
                log.append(f"  Trimmed clip {idx + 1} start to {secs}s")
        for m in _PATTERNS["trim_end"].finditer(instructions):
            idx = int(m.group(1)) - 1
            if idx < len(all_clips):
                ptr, _ = all_clips[idx]
                secs = float(m.group(2))
                length = f"{int(secs)}/1"
                proj.nodes[ptr].inputs["length_in"].value = length
                log.append(f"  Trimmed clip {idx + 1} end to {secs}s")

        # 3. TRANSITIONS
        for m in _PATTERNS["transition"].finditer(instructions):
            ttype = self._resolve_transition(m.group(1))
            dur = self._parse_duration(m.group(2))
            a = int(m.group(3)) - 1
            b = int(m.group(4)) - 1
            all_clips = self._find_clips(proj)
            if a < len(all_clips) and b < len(all_clips):
                t = proj.make_transition(ttype, dur, all_clips[a][0], all_clips[b][0])
                log.append(f"  Added {ttype} transition (ptr={t.ptr}) between clip {a + 1} and {b + 1}")
        for m in _PATTERNS["transition_simple"].finditer(instructions):
            if _PATTERNS["transition"].search(instructions):
                continue
            dur = self._parse_duration(m.group(1)) if m.lastindex and m.group(1) else "30/1"
            all_clips = self._find_clips(proj)
            if len(all_clips) >= 2:
                t = proj.make_transition("crossdissolve", dur, all_clips[-2][0], all_clips[-1][0])
                log.append(f"  Added crossdissolve transition (ptr={t.ptr}) between last two clips")

        # 4. EFFECTS (colorize, opacity, blur, transform)
        for m in list(_PATTERNS["effect"].finditer(instructions)) + list(_PATTERNS["effect_simple"].finditer(instructions)):
            raw_type = m.group(1).lower()
            clip_idx_raw = m.group(2)
            if raw_type in ("to", "on", "and") and len(all_clips) > 0:
                continue
            etype = self._resolve_effect(raw_type)
            idx = int(clip_idx_raw) - 1 if clip_idx_raw.isdigit() else 0
            params = self._extract_params(instructions)
            all_clips = self._find_clips(proj)
            if idx < len(all_clips):
                ptr = all_clips[idx][0]
                effect = proj.make_effect(etype, ptr, params)
                log.append(f"  Added {etype} effect (ptr={effect.ptr}) to clip {idx + 1} with params {params}")

        # 5. SPEED
        for m in _PATTERNS["speed"].finditer(instructions):
            all_clips = self._find_clips(proj)
            if all_clips:
                val = m.group(1)
                proj.nodes[all_clips[0][0]].inputs["speed_in"].value = val
                log.append(f"  Set clip speed to {val}x")

        # 6. EXPORT
        for m in _PATTERNS["export"].finditer(instructions):
            dst = m.group(1)
            from .export import ExportTool
            et = ExportTool()
            result = et.export(project_path, dst)
            log.append(f"  Export: {result}")

        if not log:
            log.append("No commands recognized. Try: 'add clip video.mp4 duration 10s', 'trim clip 1 start 5s', 'apply colorize to clip 1', 'add cross dissolve 1s', 'export output.mp4'")

        proj.save(project_path)
        lines = ["=== Olive Edit ==="]
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
                node = proj.make_footage(args[0])
                log.append(f"  Added footage '{args[0]}' (ptr={node.ptr})")

            elif cmd == "add_clip" and args:
                p = self._parse_kv(args)
                fp = int(p.get("footage_ptr", "0"))
                length = p.get("length", "300/1")
                ti = int(p.get("track", "0"))
                if not proj.get_node(fp):
                    log.append(f"  ERROR: footage ptr {fp} not found")
                    continue
                clip = proj.make_clip("Clip", length, fp)
                seq_ptr = self._find_sequence(proj)
                if seq_ptr:
                    self._attach_clip_to_track(proj, seq_ptr, clip, ti)
                log.append(f"  Added clip (ptr={clip.ptr}) length={length} track={ti}")

            elif cmd == "add_effect" and args:
                p = self._parse_kv(args)
                clip_ptr = int(p.get("clip_ptr", "0"))
                etype = p.get("type", "opacity")
                raw = {}
                if "params" in p:
                    for kv in p["params"].split(","):
                        if ":" in kv:
                            k, v = kv.split(":", 1)
                            raw[k.strip()] = v.strip()
                if proj.get_node(clip_ptr):
                    eff = proj.make_effect(etype, clip_ptr, raw)
                    log.append(f"  Added {etype} effect (ptr={eff.ptr}) to clip {clip_ptr}")

            elif cmd == "add_transition" and args:
                p = self._parse_kv(args)
                ca = int(p.get("clip_a", "0"))
                cb = int(p.get("clip_b", "0"))
                tt = p.get("type", "crossdissolve")
                length = p.get("length", "30/1")
                if proj.get_node(ca) and proj.get_node(cb):
                    t = proj.make_transition(tt, length, ca, cb)
                    log.append(f"  Added {tt} (ptr={t.ptr}) between {ca} and {cb}")

            elif cmd == "set_input" and args:
                p = self._parse_kv(args)
                nptr = int(p.get("node_ptr", "0"))
                iid = p.get("input", "")
                val = p.get("value", "")
                node = proj.get_node(nptr)
                if node and iid:
                    inp = node.add_input(iid, val)
                    node.inputs[iid] = inp
                    log.append(f"  Set {iid}={val} on node {nptr}")

            elif cmd == "export" and args:
                from .export import ExportTool
                result = ExportTool().export(project_path, args[0])
                log.append(f"  Export: {result}")

        proj.save(project_path)
        log.append(f"Project saved: {project_path}")
        return "\n".join(log)

    def _resolve_effect(self, name: str) -> str:
        name = name.lower().strip()
        if any(w in name for w in ("colorize", "colour", "tint", "color")):
            return "colorize"
        if any(w in name for w in ("blur", "gaussian", "soften")):
            return "blur"
        if any(w in name for w in ("transform", "scale", "rotate", "position", "move")):
            return "transform"
        return "opacity"

    def _resolve_transition(self, name: str) -> str:
        name = name.lower().strip()
        if any(w in name for w in ("dip", "fade", "color")):
            return "diptocolor"
        return "crossdissolve"

    def _parse_duration(self, s: str) -> str:
        try:
            val = float(s)
            return f"{int(val)}/1"
        except ValueError:
            return "30/1"

    def _parse_kv(self, args: list[str]) -> dict[str, str]:
        return dict(a.split("=", 1) for a in args if "=" in a)

    def _find_sequence(self, proj: OveProject) -> int | None:
        for ptr, n in proj.nodes.items():
            if "sequence" in n.node_id:
                return ptr
        return None

    def _ensure_track(self, proj: OveProject, seq_ptr: int, track_idx: int) -> int | None:
        seq = proj.get_node(seq_ptr)
        if not seq:
            return None
        for c in seq.connections:
            if c.input_id == "tex_in" and c.element == track_idx:
                if proj.get_node(c.target_ptr):
                    return c.target_ptr
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
        cur = track.inputs["block_in"].count
        track.inputs["block_in"].count = cur + 2
        track.connect("block_in", gap.ptr, element=cur)
        track.connect("block_in", clip.ptr, element=cur + 1)
