from dataclasses import dataclass, field

from app.bpmn.validator import Model, Node

SIZES = {
    "start": (36, 36),
    "end": (36, 36),
    "event": (36, 36),
    "gateway": (50, 50),
    "task": (100, 80),
    "subprocess": (100, 80),
    "data": (36, 50),
}
STORE_SIZE = (50, 50)
POOL_LABEL = 30
LANE_LABEL = 30
COL_W = 170
ROW_H = 110
PAD_X = 30
LANE_EXTRA = 40
POOL_GAP = 40

@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

@dataclass
class Layout:
    pools: list[tuple[str, Box]] = field(default_factory=list)
    lanes: dict[str, Box] = field(default_factory=dict)
    nodes: dict[str, Box] = field(default_factory=dict)
    edges: dict[int, list[tuple[float, float]]] = field(default_factory=dict)

def size_of(node: Node) -> tuple[int, int]:
    if node.icon == "store":
        return STORE_SIZE
    return SIZES[node.kind]

def split_edges(model: Model) -> tuple[list[tuple[int, str, str, str]], list[tuple[int, str, str]]]:
    flows, links = [], []
    for i, (src, dst, arrow, _) in enumerate(model.edges):
        if arrow == "-.-":
            links.append((i, src, dst))
        else:
            flows.append((i, src, dst, arrow))
    return flows, links

def find_back_edges(model: Model, flows: list[tuple[int, str, str, str]]) -> set[int]:
    out: dict[str, list[tuple[int, str]]] = {}
    for i, src, dst, _ in flows:
        out.setdefault(src, []).append((i, dst))
    order = [n.id for n in model.nodes.values() if n.kind == "start"] + list(model.nodes)
    state: dict[str, int] = {}
    back: set[int] = set()

    def visit(node: str) -> None:
        state[node] = 1
        for i, dst in out.get(node, []):
            if state.get(dst) == 1:
                back.add(i)
            elif dst not in state:
                visit(dst)
        state[node] = 2

    for node in order:
        if node not in state:
            visit(node)
    return back

def assign_columns(model: Model, flows, links, back: set[int]) -> dict[str, int]:
    inc: dict[str, list[str]] = {}
    for i, src, dst, _ in flows:
        if i not in back:
            inc.setdefault(dst, []).append(src)
    col: dict[str, int] = {}

    def depth(node: str) -> int:
        if node not in col:
            col[node] = 0
            col[node] = max((depth(p) + 1 for p in inc.get(node, [])), default=0)
        return col[node]

    for node in model.nodes.values():
        if node.kind != "data":
            depth(node.id)
    for _, a, b in links:
        data, task = (a, b) if model.nodes[a].kind == "data" else (b, a)
        col.setdefault(data, col.get(task, 0))
    for node in model.nodes.values():
        col.setdefault(node.id, 0)
    return col

def compute(model: Model) -> Layout:
    flows, links = split_edges(model)
    back = find_back_edges(model, flows)
    col = assign_columns(model, flows, links, back)
    slots: dict[str, int] = {}
    per_cell: dict[tuple[str, int], list[Node]] = {}
    for node in sorted(model.nodes.values(), key=lambda n: n.kind == "data"):
        per_cell.setdefault((node.lane, col[node.id]), []).append(node)
    lane_rows: dict[str, int] = {lane: 1 for lane in model.lanes}
    for (lane, _), nodes in per_cell.items():
        for i, node in enumerate(nodes):
            slots[node.id] = i
        lane_rows[lane] = max(lane_rows[lane], len(nodes))
    has_back: set[str] = set()
    for i in back:
        src, dst = model.edges[i][0], model.edges[i][1]
        has_back.update((model.nodes[src].lane, model.nodes[dst].lane))
    columns = max(col.values(), default=0) + 1
    pool_w = POOL_LABEL + LANE_LABEL + PAD_X + columns * COL_W
    layout = Layout()
    y = 0.0
    for name, lanes in model.pools:
        top = y
        for lane in lanes:
            h = lane_rows[lane] * ROW_H + (LANE_EXTRA if lane in has_back else 0)
            layout.lanes[lane] = Box(POOL_LABEL, y, pool_w - POOL_LABEL, h)
            for node in model.nodes.values():
                if node.lane != lane:
                    continue
                w, nh = size_of(node)
                cx = POOL_LABEL + LANE_LABEL + PAD_X + col[node.id] * COL_W + COL_W / 2
                cy = y + slots[node.id] * ROW_H + ROW_H / 2
                layout.nodes[node.id] = Box(cx - w / 2, cy - nh / 2, w, nh)
            y += h
        layout.pools.append((name, Box(0, top, pool_w, y - top)))
        y += POOL_GAP
    for i, src, dst, arrow in flows:
        layout.edges[i] = route(model, layout, col, i in back, src, dst, arrow == "-.->")
    for i, src, dst in links:
        layout.edges[i] = route_link(layout, src, dst)
    return layout

def route(model: Model, layout: Layout, col, is_back: bool, src: str, dst: str, message: bool) -> list[tuple[float, float]]:
    a, b = layout.nodes[src], layout.nodes[dst]
    if message:
        if b.y >= a.bottom:
            start, end = (a.cx, a.bottom), (b.cx, b.y)
        else:
            start, end = (a.cx, a.y), (b.cx, b.bottom)
        mid = (start[1] + end[1]) / 2
        return [start, (start[0], mid), (end[0], mid), end]
    if is_back or col[dst] <= col[src]:
        lane_bottom = max(layout.lanes[model.nodes[src].lane].bottom, layout.lanes[model.nodes[dst].lane].bottom)
        yb = min(max(a.bottom, b.bottom) + 25, lane_bottom - 8)
        return [(a.cx, a.bottom), (a.cx, yb), (b.cx, yb), (b.cx, b.bottom)]
    if abs(a.cy - b.cy) < 1:
        return [(a.right, a.cy), (b.x, b.cy)]
    if model.nodes[src].kind == "gateway":
        edge = a.bottom if b.cy > a.cy else a.y
        return [(a.cx, edge), (a.cx, b.cy), (b.x, b.cy)]
    if model.nodes[dst].kind == "gateway":
        edge = b.y if a.cy < b.cy else b.bottom
        return [(a.right, a.cy), (b.cx, a.cy), (b.cx, edge)]
    mx = b.x - 25
    return [(a.right, a.cy), (mx, a.cy), (mx, b.cy), (b.x, b.cy)]

def route_link(layout: Layout, src: str, dst: str) -> list[tuple[float, float]]:
    a, b = layout.nodes[src], layout.nodes[dst]
    down = b.cy > a.cy
    start = (a.cx, a.bottom if down else a.y)
    end = (b.cx, b.y if down else b.bottom)
    if abs(a.cx - b.cx) < 1:
        return [start, end]
    mid = (start[1] + end[1]) / 2
    return [start, (start[0], mid), (end[0], mid), end]
