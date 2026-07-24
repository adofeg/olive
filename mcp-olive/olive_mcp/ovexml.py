import copy
import uuid
from pathlib import Path
from xml.etree import ElementTree as ET



_NODE_IDS = {
    "folder": "org.olivevideoeditor.Olive.folder",
    "footage": "org.olivevideoeditor.Olive.footage",
    "sequence": "org.olivevideoeditor.Olive.sequence",
    "track": "org.olivevideoeditor.Olive.track",
    "clip": "org.olivevideoeditor.Olive.clip",
    "gap": "org.olivevideoeditor.Olive.gap",
    "crossdissolve": "org.olivevideoeditor.Olive.crossdissolve",
    "diptocolor": "org.olivevideoeditor.Olive.diptocolor",
    "opacity": "org.olivevideoeditor.Olive.opacity",
    "transform": "org.olivevideoeditor.Olive.transform",
    "colorize": "org.olivevideoeditor.Olive.colorize",
    "solid": "org.olivevideoeditor.Olive.solid",
    "textv3": "org.olivevideoeditor.Olive.textv3",
    "shape": "org.olivevideoeditor.Olive.shape",
}


class _Ptr:
    _next = 1000
    _reserved: set[int] = set()

    @classmethod
    def reset(cls):
        cls._next = 1000
        cls._reserved.clear()

    @classmethod
    def reserve(cls, ptr: int):
        cls._reserved.add(ptr)
        if ptr >= cls._next:
            cls._next = ptr + 1

    @classmethod
    def next(cls) -> int:
        cls._next += 1
        while cls._next in cls._reserved:
            cls._next += 1
        return cls._next


class OveNode:
    def __init__(self, node_id: str, name: str = ""):
        self.ptr = _Ptr.next()
        self.node_id = node_id
        self.name = name
        self.inputs: dict[str, "OveInput"] = {}
        self.connections: list["OveConnection"] = []
        self.custom: ET.Element | None = None
        self.links: list[int] = []
        self.uuid1 = str(uuid.uuid4())
        self.uuid2 = str(uuid.uuid4())

    def add_input(self, input_id: str, value: str = "", keyframing: int = 0):
        inp = OveInput(input_id, value, keyframing)
        self.inputs[input_id] = inp
        return inp

    def add_array_input(self, input_id: str, count: int = 0):
        inp = OveArrayInput(input_id, count)
        self.inputs[input_id] = inp
        return inp

    def connect(self, input_id: str, target_ptr: int, element: int = -1):
        self.connections.append(OveConnection(input_id, target_ptr, element))

    def to_xml(self) -> ET.Element:
        e = ET.Element("node", version="1", id=self.node_id, ptr=str(self.ptr))
        if self.name:
            e.set("name", self.name)

        for inp in self.inputs.values():
            e.append(inp.to_xml())

        if self.connections:
            conns = ET.SubElement(e, "connections")
            for c in self.connections:
                conns.append(c.to_xml())

        if self.custom is not None:
            e.append(self.custom)
        else:
            ET.SubElement(e, "custom")

        return e


class OveInput:
    def __init__(self, input_id: str, value: str = "", keyframing: int = 0):
        self.input_id = input_id
        self.value = value
        self.keyframing = keyframing

    def to_xml(self) -> ET.Element:
        inp = ET.Element("input", id=self.input_id)
        primary = ET.SubElement(inp, "primary")
        ET.SubElement(primary, "keyframing").text = str(self.keyframing)
        std = ET.SubElement(primary, "standard")
        t = ET.SubElement(std, "track")
        if self.value:
            t.text = self.value
        return inp

    def _make_primary_with_child(self, child: ET.Element) -> ET.Element:
        primary = ET.Element("primary")
        ET.SubElement(primary, "keyframing").text = str(self.keyframing)
        std = ET.SubElement(primary, "standard")
        std.append(child)
        return primary

    def _set_direct_text(self, text: str):
        self.value = text


class OveArrayInput:
    def __init__(self, input_id: str, count: int = 0):
        self.input_id = input_id
        self.count = count

    def to_xml(self) -> ET.Element:
        inp = ET.Element("input", id=self.input_id)
        primary = ET.SubElement(inp, "primary")
        ET.SubElement(primary, "keyframing").text = "0"
        std = ET.SubElement(primary, "standard")
        ET.SubElement(std, "track")
        subs = ET.SubElement(inp, "subelements", count=str(self.count))
        for _ in range(self.count):
            el = ET.SubElement(subs, "element")
            ET.SubElement(el, "keyframing").text = "0"
            s = ET.SubElement(el, "standard")
            ET.SubElement(s, "track")
        return inp


class OveConnection:
    def __init__(self, input_id: str, target_ptr: int, element: int = -1):
        self.input_id = input_id
        self.target_ptr = target_ptr
        self.element = element

    def to_xml(self) -> ET.Element:
        c = ET.Element("connection", input=self.input_id, element=str(self.element))
        ET.SubElement(c, "output").text = str(self.target_ptr)
        return c


class OveProject:
    SERIALIZER_VERSION = "230220"

    def __init__(self):
        self.nodes: dict[int, OveNode] = {}
        self.project_uuid = str(uuid.uuid4())
        self.root_folder_ptr: int | None = None

    def add_node(self, node: OveNode) -> OveNode:
        self.nodes[node.ptr] = node
        return node

    def get_node(self, ptr: int) -> OveNode | None:
        return self.nodes.get(ptr)

    def make_clip(self, name: str, length: str, media_ptr: int, media_in: str = "0/1", speed: str = "1") -> OveNode:
        node = OveNode(_NODE_IDS["clip"], name)
        node.add_input("length_in", length)
        node.add_input("media_in_in", media_in)
        node.add_input("speed_in", speed)
        node.add_input("reverse_in", "0")
        node.add_input("maintain_audio_pitch_in", "0")
        node.add_input("autocache_in", "1")
        node.add_input("loop_in", "0")
        node.add_input("buffer_in")
        node.add_input("enabled_in", "1")
        node.connect("buffer_in", media_ptr)
        self.add_node(node)
        return node

    def make_gap(self, length: str) -> OveNode:
        node = OveNode(_NODE_IDS["gap"])
        node.add_input("length_in", length)
        node.add_input("enabled_in", "1")
        self.add_node(node)
        return node

    def make_track(self, name: str, blocks: list[OveNode] | None = None) -> OveNode:
        node = OveNode(_NODE_IDS["track"], name)
        node.add_input("muted_in", "0")
        node.add_input("enabled_in", "1")
        blocks = blocks or []
        arr = node.add_array_input("block_in", len(blocks))
        for i, blk in enumerate(blocks):
            node.connect("block_in", blk.ptr, element=i)
        custom = ET.Element("custom")
        ET.SubElement(custom, "height").text = "3"
        node.custom = custom
        self.add_node(node)
        return node

    def make_sequence(self, name: str, width: int = 1920, height: int = 1080,
                      fr_num: int = 30, fr_den: int = 1,
                      video_tracks: list[OveNode] | None = None,
                      audio_tracks: list[OveNode] | None = None) -> OveNode:
        node = OveNode(_NODE_IDS["sequence"], name)

        vp = node.add_input("video_params")
        vp.value = ""
        custom_vp = ET.fromstring(
            f'<standard_value width="{width}" height="{height}" format="0" '
            f'pixel_aspect_ratio="1" interlacing="0" divider="0" '
            f'frame_rate_numerator="{fr_num}" frame_rate_denominator="{fr_den}" '
            f'color_range="0"/>'
        )
        primary_vp = node.inputs["video_params"]._make_primary_with_child(custom_vp)

        ap = node.add_input("audio_params")
        ap.value = ""
        custom_ap = ET.fromstring(
            '<standard_value sample_rate="48000" channel_layout="3" format="1"/>'
        )
        primary_ap = node.inputs["audio_params"]._make_primary_with_child(custom_ap)

        vts = video_tracks or []
        ats = audio_tracks or []
        tex_arr = node.add_array_input("tex_in", len(vts))
        for i, t in enumerate(vts):
            node.connect("tex_in", t.ptr, element=i)

        sam_arr = node.add_array_input("samples_in", len(ats))
        for i, t in enumerate(ats):
            node.connect("samples_in", t.ptr, element=i)

        self.add_node(node)
        return node

    def make_footage(self, file_path: str, name: str = "") -> OveNode:
        node = OveNode(_NODE_IDS["footage"], name or Path(file_path).stem)
        fn = node.add_input("filename")
        fn._set_direct_text(str(file_path))
        node.add_input("video_params")
        node.add_input("audio_params")
        node.add_input("subtitle_params")
        vp_std = ET.fromstring(
            '<standard_value width="0" height="0" format="0" '
            'pixel_aspect_ratio="1" interlacing="0" divider="0" '
            'frame_rate_numerator="0" frame_rate_denominator="0" '
            'color_range="0"/>'
        )
        node.inputs["video_params"]._make_primary_with_child(vp_std)
        ap_std = ET.fromstring(
            '<standard_value sample_rate="0" channel_layout="0" format="0"/>'
        )
        node.inputs["audio_params"]._make_primary_with_child(ap_std)
        self.add_node(node)
        return node

    def make_transition(self, trans_type: str, length: str,
                        out_clip_ptr: int, in_clip_ptr: int,
                        center: str = "0/1") -> OveNode:
        tid = _NODE_IDS.get(trans_type, _NODE_IDS["crossdissolve"])
        node = OveNode(tid)
        node.add_input("length_in", length)
        node.add_input("center_in", center)
        node.add_input("curve_in", "0")
        node.add_input("enabled_in", "1")
        node.connect("out_block_in", out_clip_ptr)
        node.connect("in_block_in", in_clip_ptr)
        self.add_node(node)
        return node

    def make_text(self, text: str, position: str = "0,0", size: str = "48") -> OveNode:
        node = OveNode(_NODE_IDS["textv3"], "Text")
        node.add_input("tex_in")
        node.add_input("enabled_in", "1")
        node.add_input("text_in", text)
        node.add_input("halign_in", "1")
        node.add_input("valign_in", "1")
        node.add_input("size_in", size)
        node.add_input("color_in", "1.0,1.0,1.0,1.0")
        node.add_input("position_in", position)
        self.add_node(node)
        return node

    def make_effect(self, effect_type: str, texture_ptr: int, params: dict[str, str] | None = None) -> OveNode:
        eid = _NODE_IDS.get(effect_type, effect_type)
        node = OveNode(eid)
        node.add_input("tex_in")
        node.add_input("enabled_in", "1")
        node.connect("tex_in", texture_ptr)
        if params:
            for k, v in params.items():
                node.add_input(k, v)
        effect_inputs = {
            "opacity": {"val_in": "1.0"},
            "colorize": {"color_in": "0.5,0.5,0.5,1.0", "saturation_in": "0.5", "strength_in": "1.0", "preserve_luminosity_in": "1"},
            "transform": {},
        }
        defaults = effect_inputs.get(effect_type, {})
        for k, v in defaults.items():
            if k not in (params or {}):
                node.add_input(k, v)
        self.add_node(node)
        return node

    def to_xml(self) -> ET.Element:
        root = ET.Element("project", version=self.SERIALIZER_VERSION)
        proj = ET.SubElement(root, "project", version="1")
        ET.SubElement(proj, "uuid").text = self.project_uuid
        nodes_wrapper = ET.SubElement(proj, "nodes")
        for n in self.nodes.values():
            nodes_wrapper.append(n.to_xml())
        settings = ET.SubElement(proj, "settings")
        ET.SubElement(settings, "root").text = str(self.root_folder_ptr or 1)
        ET.SubElement(settings, "cachesetting").text = "0"
        ET.SubElement(settings, "cachesettingpath")
        ET.SubElement(settings, "color_config_filename")
        ET.SubElement(settings, "color_reference_space").text = "aces 1.0 sdr video"
        layout = ET.SubElement(root, "layout")
        ET.SubElement(layout, "mainwindow")
        return root

    def to_string(self) -> str:
        rough = ET.tostring(self.to_xml(), encoding="unicode")
        return self._indent_xml(rough)

    @staticmethod
    def _indent_xml(xml_str: str) -> str:
        lines = []
        indent = 0
        for line in xml_str.split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("</"):
                indent -= 1
            lines.append("  " * indent + line)
            if line.startswith("<") and not line.startswith("</") and not line.endswith("/>"):
                indent += 1
        return "\n".join(lines)

    def save(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_string())

    def load(self, path: str):
        tree = ET.parse(path)
        root = tree.getroot()
        self.nodes.clear()
        proj = root.find("project")
        if proj is None:
            proj = root
        uuid_el = proj.find("uuid")
        if uuid_el is not None:
            self.project_uuid = uuid_el.text or self.project_uuid
        nodes_wrapper = proj.find("nodes")
        if nodes_wrapper is not None:
            for node_el in nodes_wrapper.findall("node"):
                ptr = int(node_el.get("ptr", "0"))
                _Ptr.reserve(ptr)
                self._load_node(node_el)

    def _load_node(self, el: ET.Element):
        node_id = el.get("id", "")
        name = el.get("name", "")
        ptr = int(el.get("ptr", "0"))
        node = OveNode(node_id, name)
        node.ptr = ptr
        for inp_el in el.findall("input"):
            iid = inp_el.get("id", "")
            primary = inp_el.find("primary")
            val = ""
            if primary is not None:
                std = primary.find("standard")
                if std is not None:
                    t = std.find("track")
                    if t is not None and t.text:
                        val = t.text
            subs = inp_el.find("subelements")
            if subs is not None:
                count = int(subs.get("count", "0"))
                arr = OveArrayInput(iid, count)
                node.inputs[iid] = arr
            else:
                node.inputs[iid] = OveInput(iid, val)
        conns_el = el.find("connections")
        if conns_el is not None:
            for c_el in conns_el.findall("connection"):
                inp_id = c_el.get("input", "")
                elem = int(c_el.get("element", "-1"))
                out_el = c_el.find("output")
                if out_el is not None and out_el.text:
                    target = int(out_el.text)
                    node.connections.append(OveConnection(inp_id, target, elem))
        custom_el = el.find("custom")
        if custom_el is not None:
            node.custom = copy.deepcopy(custom_el)
        self.nodes[ptr] = node


