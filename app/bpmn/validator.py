import json
import re
from dataclasses import dataclass, field
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "web"
ICONS = set(json.loads((WEB / "icons.json").read_text()))
TASK_ICONS = {
    "user", "hand", "gear", "scroll", "table-list", "envelope", "envelope-open",
    "truck", "building", "file", "database", "credit-card", "phone", "calculator",
}
GATEWAYS = {"xor", "and", "or", "event-based"}
ID = r"[A-Za-z][A-Za-z0-9_]*"
HEADER = re.compile(r"^swimlane-beta\s+LR$")
POOL = re.compile(r"^%%\s*pool\s*:\s*(.+?)\s*\|\s*(.+)$", re.I)
LANE = re.compile(rf'^subgraph\s+({ID})\s*\[\s*"([^"]+)"\s*\]$')
NODE_AT = re.compile(rf"^({ID})@\{{(.*)\}}$")
TASK = re.compile(rf'^({ID})\(\s*"([^"]*)"\s*\)$')
SUB = re.compile(rf'^({ID})\[\[\s*"([^"]*)"\s*\]\]$')
STORE = re.compile(rf'^({ID})\[\(\s*"([^"]*)"\s*\)\]$')
ARROW = re.compile(r"\s*(-->|-\.->|-\.-)(?:\|([^|]*)\|)?\s*")
MAX_ERRORS = 12

@dataclass
class Node:
    id: str
    kind: str
    lane: str
    icon: str = ""
    name: str = ""

@dataclass
class Model:
    lanes: list[str] = field(default_factory=list)
    lane_names: dict[str, str] = field(default_factory=dict)
    pools: list[tuple[str, list[str]]] = field(default_factory=list)
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[tuple[str, str, str, str]] = field(default_factory=list)

def _parse_at(nid: str, body: str, lane: str, n: int, errors: list[str]) -> Node | None:
    shape = re.search(r"shape\s*:\s*([\w-]+)", body)
    label = re.search(r'label\s*:\s*"([^"]*)"', body)
    if not shape or not label:
        errors.append(f"line {n}: {nid} must have shape and label in double quotes")
        return None
    if shape.group(1) == "doc":
        return Node(nid, "data", lane, "doc", label.group(1))
    if shape.group(1) != "icon":
        errors.append(f"line {n}: shape '{shape.group(1)}' is not supported, allowed: icon and doc")
        return None
    icon = re.search(r'icon\s*:\s*"bpmn:([\w-]+)"', body)
    if not icon or icon.group(1) not in ICONS:
        errors.append(f"line {n}: icon of {nid} must be one of bpmn:{{{', '.join(sorted(ICONS))}}}")
        return None
    name = icon.group(1)
    head = name.split("-")[0]
    kind = {"start": "start", "end": "end"}.get(head, "gateway" if name in GATEWAYS else "event")
    return Node(nid, kind, lane, name, label.group(1))

def parse(mmd: str) -> tuple[Model, list[str]]:
    model = Model()
    errors: list[str] = []
    lane = ""
    header_seen = False
    pool_lines: list[tuple[str, list[str]]] = []
    for n, raw in enumerate(mmd.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        pool = POOL.match(line)
        if pool:
            pool_lines.append((pool.group(1), [s.strip() for s in pool.group(2).split(",") if s.strip()]))
            continue
        if line.startswith("%%"):
            continue
        if not header_seen:
            header_seen = True
            if not HEADER.match(line):
                errors.append("the first line must be exactly: swimlane-beta LR")
            continue
        if line == "end":
            if not lane:
                errors.append(f"line {n}: unexpected end")
            lane = ""
            continue
        if line.startswith("subgraph"):
            if lane:
                errors.append(f"line {n}: nested subgraph is forbidden, lane {lane} is not closed with end")
            m = LANE.match(line)
            if not m:
                errors.append(f'line {n}: a lane must look like subgraph L1["Name"]')
                lane = "?"
                continue
            lane = m.group(1)
            if lane in model.lanes:
                errors.append(f"line {n}: lane {lane} is declared twice")
            model.lanes.append(lane)
            model.lane_names[lane] = m.group(2)
            continue
        if lane:
            node = None
            at, task, sub, store = NODE_AT.match(line), TASK.match(line), SUB.match(line), STORE.match(line)
            if at:
                node = _parse_at(at.group(1), at.group(2), lane, n, errors)
            elif task:
                icon = re.match(r"fa:fa-([\w-]+)\s+\S", task.group(2))
                if icon and icon.group(1) not in TASK_ICONS:
                    errors.append(f"line {n}: icon fa:fa-{icon.group(1)} is not supported")
                text = task.group(2)
                node = Node(task.group(1), "task", lane, icon.group(1) if icon else "", text[icon.end() - 1:].strip() if icon else text.strip())
            elif sub:
                node = Node(sub.group(1), "subprocess", lane, "", sub.group(2))
            elif store:
                node = Node(store.group(1), "data", lane, "store", store.group(2))
            else:
                errors.append(f"line {n}: unrecognized element inside a lane: {line}")
                continue
            if node:
                if node.id in model.nodes:
                    errors.append(f"line {n}: id {node.id} is used more than once")
                model.nodes[node.id] = node
            continue
        parts = ARROW.split(line)
        if len(parts) < 3:
            errors.append(f"line {n}: {line} is declared outside a lane or is not a flow")
            continue
        for i in range(0, len(parts) - 1, 3):
            src, arrow, label, dst = parts[i].strip(), parts[i + 1], (parts[i + 2] or "").strip(), parts[i + 3].strip()
            model.edges.append((src, dst, arrow, label))
    if not header_seen:
        errors.append("the diagram is empty")
    if lane:
        errors.append(f"lane {lane} is not closed with end")
    model.pools = pool_lines
    return model, errors

def _check_pools(model: Model, errors: list[str]) -> dict[str, str]:
    lane_pool: dict[str, str] = {}
    if not model.pools:
        errors.append("no pool lines: add after the first line: %% pool: Pool name | L1, L2")
        return {lane: "pool" for lane in model.lanes}
    for name, lanes in model.pools:
        idx = []
        for lane in lanes:
            if lane not in model.lanes:
                errors.append(f"pool {name} references a lane that does not exist: {lane}")
            elif lane in lane_pool:
                errors.append(f"lane {lane} belongs to several pools")
            else:
                lane_pool[lane] = name
                idx.append(model.lanes.index(lane))
        if idx and sorted(idx) != list(range(min(idx), min(idx) + len(idx))):
            errors.append(f"lanes of pool {name} must follow each other in the document")
    for lane in model.lanes:
        if lane not in lane_pool:
            errors.append(f"lane {lane} does not belong to any pool")
    return lane_pool

def validate(mmd: str) -> list[str]:
    model, errors = parse(mmd)
    lane_pool = _check_pools(model, errors)
    out: dict[str, int] = {}
    inc: dict[str, int] = {}
    labels_out: dict[str, list[str]] = {}
    for src, dst, arrow, label in model.edges:
        missing = [x for x in (src, dst) if not re.fullmatch(ID, x) or x not in model.nodes]
        if missing:
            errors.append(f"flow {src} {arrow} {dst} uses an undeclared element: {', '.join(missing)} (declare elements only inside lanes, flows may contain ids only)")
            continue
        a, b = model.nodes[src], model.nodes[dst]
        same_pool = lane_pool.get(a.lane) == lane_pool.get(b.lane)
        if arrow == "-->":
            if not same_pool:
                errors.append(f"sequence flow {src} --> {dst} crosses pools, use a message flow -.->")
            if "data" in (a.kind, b.kind):
                errors.append(f"data {src}/{dst} must be connected with an association -.-, not -->")
        elif arrow == "-.->":
            if same_pool:
                errors.append(f"message flow {src} -.-> {dst} is inside one pool, use -->")
            if not label:
                errors.append(f"message flow {src} -.-> {dst} has no label")
        elif "data" not in (a.kind, b.kind):
            errors.append(f"association {src} -.- {dst} is allowed only with data elements")
        if arrow != "-.-":
            out[src] = out.get(src, 0) + 1
            inc[dst] = inc.get(dst, 0) + 1
            labels_out.setdefault(src, []).append(label)
        else:
            out.setdefault(src, 0)
    for node in model.nodes.values():
        if node.kind == "data":
            continue
        if node.kind == "start" and inc.get(node.id):
            errors.append(f"start event {node.id} cannot have an incoming flow")
        elif node.kind != "start" and not inc.get(node.id):
            errors.append(f"element {node.id} has no incoming flow")
        if node.kind == "end" and out.get(node.id):
            errors.append(f"end event {node.id} cannot have an outgoing flow")
        elif node.kind != "end" and not out.get(node.id):
            errors.append(f"element {node.id} has no outgoing flow")
        if node.icon in {"xor", "or"} and out.get(node.id, 0) >= 2 and not all(labels_out[node.id]):
            errors.append(f"all outgoing arrows of gateway {node.id} must have condition labels")
        if node.kind == "gateway" and node.icon != "event-based" and out.get(node.id) == 1 and inc.get(node.id, 0) <= 1:
            errors.append(f"gateway {node.id} neither splits nor merges anything")
    kinds = {n.kind for n in model.nodes.values()}
    if "start" not in kinds:
        errors.append("there is no start event")
    if "end" not in kinds:
        errors.append("there is no end event")
    if not model.edges:
        errors.append("there are no flows")
    return errors[:MAX_ERRORS]
