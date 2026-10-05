import re

from app.bpmn.validator import LANE, Model, parse

LABEL_CLEAN = re.compile(r'[|"\[\]{}]')

def lane_blocks(mmd: str) -> dict[str, list[str]]:
    blocks: dict[str, list[str]] = {}
    current = ""
    for raw in mmd.splitlines():
        line = raw.strip()
        match = LANE.match(line)
        if match:
            current = match.group(1)
            blocks.setdefault(current, [])
        elif line == "end":
            current = ""
        elif current and line and not line.startswith("%%"):
            blocks[current].append(line)
    return blocks

def arrange_pools(model: Model) -> list[tuple[str, list[str]]]:
    seen: set[str] = set()
    pools: list[tuple[str, list[str]]] = []
    for name, lanes in model.pools:
        kept = [lane for lane in lanes if lane in model.lanes and lane not in seen]
        seen.update(kept)
        if kept:
            pools.append((name, kept))
    rest = [lane for lane in model.lanes if lane not in seen]
    if not pools and rest:
        return [("Process", rest)]
    return pools + [(model.lane_names[lane], [lane]) for lane in rest]

def clean_label(text: str) -> str:
    return LABEL_CLEAN.sub("", text).strip()

def fix_edges(model: Model, lane_pool: dict[str, int]) -> list[tuple[str, str, str, str]]:
    edges: list[tuple[str, str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for src, dst, arrow, label in model.edges:
        if src not in model.nodes or dst not in model.nodes or src == dst:
            continue
        a, b = model.nodes[src], model.nodes[dst]
        has_data = "data" in (a.kind, b.kind)
        if has_data:
            arrow, label = "-.-", ""
        elif arrow == "-.-":
            continue
        elif a.kind == "end" or b.kind == "start":
            continue
        elif lane_pool[a.lane] != lane_pool[b.lane]:
            arrow, label = "-.->", clean_label(label) or clean_label(b.name)[:40] or "Message"
        else:
            arrow = "-->"
        key = (src, dst, arrow)
        if key in seen:
            continue
        seen.add(key)
        edges.append((src, dst, arrow, clean_label(label)))
    return edges

def complete_ends(model: Model, edges: list[tuple[str, str, str, str]], lane_pool: dict[str, int]) -> dict[str, list[str]]:
    extra: dict[str, list[str]] = {lane: [] for lane in model.lanes}
    out = {e[0] for e in edges if e[2] != "-.-"}
    inc = {e[1] for e in edges if e[2] != "-.-"}
    counter = 0
    order = list(model.nodes)
    dead = [n for n in model.nodes.values() if n.kind not in {"data", "end", "gateway"} and n.id not in out]
    for orphan in model.nodes.values():
        if orphan.kind in {"data", "start"} or orphan.id in inc:
            continue
        before = [d for d in dead if order.index(d.id) < order.index(orphan.id) and lane_pool[d.lane] == lane_pool[orphan.lane]]
        if before:
            edges.append((before[-1].id, orphan.id, "-->", ""))
            dead.remove(before[-1])
            out.add(before[-1].id)
            inc.add(orphan.id)
    for node in model.nodes.values():
        if node.kind in {"data", "end"} or node.id in out:
            continue
        counter += 1
        end_id = f"autoend{counter}"
        extra[node.lane].append(f'{end_id}@{{ shape: icon, icon: "bpmn:end", label: "End", pos: "b", h: 40 }}')
        edges.append((node.id, end_id, "-->", ""))
        out.add(node.id)
        inc.add(end_id)
    pools_with_start = {lane_pool[n.lane] for n in model.nodes.values() if n.kind == "start"}
    for node in list(model.nodes.values()):
        pool = lane_pool[node.lane]
        if node.kind in {"data", "start"} or node.id in inc or pool in pools_with_start:
            continue
        counter += 1
        start_id = f"autostart{counter}"
        extra[node.lane].append(f'{start_id}@{{ shape: icon, icon: "bpmn:start", label: "Start", pos: "b", h: 40 }}')
        edges.insert(0, (start_id, node.id, "-->", ""))
        pools_with_start.add(pool)
    return extra

def format_edge(src: str, dst: str, arrow: str, label: str) -> str:
    if label and arrow != "-.-":
        return f"{src} {arrow}|{label}| {dst}"
    return f"{src} {arrow} {dst}"

def drop_idle_gateways(model: Model, edges: list[tuple[str, str, str, str]], blocks: dict[str, list[str]]) -> None:
    for node in list(model.nodes.values()):
        if node.kind != "gateway" or node.icon == "event-based":
            continue
        incoming = [e for e in edges if e[1] == node.id and e[2] != "-.-"]
        outgoing = [e for e in edges if e[0] == node.id and e[2] != "-.-"]
        if len(incoming) != 1 or len(outgoing) != 1:
            continue
        src, dst = incoming[0][0], outgoing[0][1]
        arrow = "-->" if incoming[0][2] == outgoing[0][2] else outgoing[0][2]
        edges.remove(incoming[0])
        edges.remove(outgoing[0])
        edges.append((src, dst, arrow, incoming[0][3] or outgoing[0][3]))
        blocks[node.lane] = [line for line in blocks[node.lane] if not line.startswith(f"{node.id}@")]
        del model.nodes[node.id]

def drop_orphan_ends(model: Model, edges: list[tuple[str, str, str, str]], blocks: dict[str, list[str]]) -> None:
    linked = {e[1] for e in edges if e[2] != "-.-"}
    for node in list(model.nodes.values()):
        if node.kind == "end" and node.id not in linked:
            blocks[node.lane] = [line for line in blocks[node.lane] if not line.startswith(f"{node.id}@")]
            edges[:] = [e for e in edges if node.id not in e[:2]]
            del model.nodes[node.id]

def repair(mmd: str) -> str:
    model, errors = parse(mmd)
    if [e for e in errors if "declared twice" not in e] or not model.lanes:
        return mmd
    model.lanes = list(dict.fromkeys(model.lanes))
    pools = arrange_pools(model)
    lane_pool = {lane: i for i, (_, lanes) in enumerate(pools) for lane in lanes}
    edges = fix_edges(model, lane_pool)
    blocks = lane_blocks(mmd)
    drop_idle_gateways(model, edges, blocks)
    drop_orphan_ends(model, edges, blocks)
    extra = complete_ends(model, edges, lane_pool)
    lines = ["swimlane-beta LR"]
    lines += [f"%% pool: {name} | {', '.join(lanes)}" for name, lanes in pools]
    for _, lanes in pools:
        for lane in lanes:
            lines.append(f'subgraph {lane}["{model.lane_names[lane]}"]')
            lines += [f"  {line}" for line in blocks[lane] + extra[lane]]
            lines.append("end")
    lines += [format_edge(*edge) for edge in edges]
    return "\n".join(lines)
