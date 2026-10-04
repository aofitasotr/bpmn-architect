import xml.etree.ElementTree as ET

from app.bpmn.layout import Box, Layout, compute
from app.bpmn.validator import Model, Node, parse

NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)

TASKS = {
    "user": "userTask",
    "hand": "manualTask",
    "gear": "serviceTask",
    "scroll": "scriptTask",
    "table-list": "businessRuleTask",
    "envelope": "sendTask",
    "envelope-open": "receiveTask",
}
GATEWAYS = {
    "xor": "exclusiveGateway",
    "and": "parallelGateway",
    "or": "inclusiveGateway",
    "event-based": "eventBasedGateway",
}
DEFINITIONS = {
    "message": "messageEventDefinition",
    "timer": "timerEventDefinition",
    "signal": "signalEventDefinition",
    "condition": "conditionalEventDefinition",
    "error": "errorEventDefinition",
    "terminate": "terminateEventDefinition",
}

def q(prefix: str, name: str) -> str:
    return f"{{{NS[prefix]}}}{name}"

def element(parent: ET.Element, tag: str, **attrs) -> ET.Element:
    return ET.SubElement(parent, q("bpmn", tag), {k: str(v) for k, v in attrs.items() if v != ""})

def event_tag(node: Node) -> tuple[str, str]:
    head, _, kind = node.icon.partition("-")
    if head == "start":
        return "startEvent", kind
    if head == "end":
        return "endEvent", kind
    if head == "catch":
        return "intermediateCatchEvent", kind
    return "intermediateThrowEvent", kind

def flow_node_tag(node: Node) -> str:
    if node.kind == "task":
        return TASKS.get(node.icon, "task")
    if node.kind == "subprocess":
        return "subProcess"
    if node.kind == "gateway":
        return GATEWAYS[node.icon]
    return event_tag(node)[0]

def add_flow_node(process: ET.Element, node: Node, incoming: dict, outgoing: dict) -> None:
    if node.kind == "data":
        return
    el = element(process, flow_node_tag(node), id=node.id, name=node.name)
    for flow_id in incoming.get(node.id, []):
        element(el, "incoming").text = flow_id
    for flow_id in outgoing.get(node.id, []):
        element(el, "outgoing").text = flow_id
    if node.kind in {"start", "end", "event"}:
        definition = DEFINITIONS.get(event_tag(node)[1])
        if definition:
            d = element(el, definition)
            if definition == "conditionalEventDefinition":
                cond = ET.SubElement(d, q("bpmn", "condition"))
                cond.set(q("xsi", "type"), "bpmn:tFormalExpression")

def build(model: Model, layout: Layout) -> ET.Element:
    root = ET.Element(q("bpmn", "definitions"), {
        "id": "Definitions_1",
        "targetNamespace": "http://bpmn.io/schema/bpmn",
    })
    pool_of = {lane: i for i, (_, lanes) in enumerate(model.pools) for lane in lanes}
    flow_ids: dict[int, str] = {}
    incoming: dict[str, list[str]] = {}
    outgoing: dict[str, list[str]] = {}
    for i, (src, dst, arrow, _) in enumerate(model.edges):
        if arrow == "-.-":
            flow_ids[i] = f"Association_{i + 1}"
            continue
        flow_ids[i] = f"MessageFlow_{i + 1}" if arrow == "-.->" else f"Flow_{i + 1}"
        if arrow == "-->":
            outgoing.setdefault(src, []).append(flow_ids[i])
            incoming.setdefault(dst, []).append(flow_ids[i])
    collaboration = element(root, "collaboration", id="Collaboration_1")
    for i, (name, _) in enumerate(model.pools):
        element(collaboration, "participant", id=f"Participant_{i + 1}", name=name, processRef=f"Process_{i + 1}")
    for i, (src, dst, arrow, label) in enumerate(model.edges):
        if arrow == "-.->":
            element(collaboration, "messageFlow", id=flow_ids[i], name=label, sourceRef=src, targetRef=dst)
    stores = [n for n in model.nodes.values() if n.icon == "store"]
    for node in stores:
        element(root, "dataStore", id=f"DataStore_{node.id}", name=node.name)
    for p, (name, lanes) in enumerate(model.pools):
        process = element(root, "process", id=f"Process_{p + 1}", name=name, isExecutable="false")
        lane_set = element(process, "laneSet", id=f"LaneSet_{p + 1}")
        for lane in lanes:
            el = element(lane_set, "lane", id=lane, name=model.lane_names[lane])
            for node in model.nodes.values():
                if node.lane == lane:
                    element(el, "flowNodeRef").text = node.id
        members = [n for n in model.nodes.values() if pool_of[n.lane] == p]
        for node in members:
            add_flow_node(process, node, incoming, outgoing)
        for node in members:
            if node.icon == "store":
                element(process, "dataStoreReference", id=node.id, name=node.name, dataStoreRef=f"DataStore_{node.id}")
            elif node.kind == "data":
                element(process, "dataObject", id=f"DataObject_{node.id}", name=node.name)
                element(process, "dataObjectReference", id=node.id, name=node.name, dataObjectRef=f"DataObject_{node.id}")
        for i, (src, dst, arrow, label) in enumerate(model.edges):
            if arrow == "-->" and pool_of[model.nodes[src].lane] == p:
                element(process, "sequenceFlow", id=flow_ids[i], name=label, sourceRef=src, targetRef=dst)
        for i, (src, dst, arrow, _) in enumerate(model.edges):
            if arrow == "-.-" and pool_of[model.nodes[src].lane] == p:
                element(process, "association", id=flow_ids[i], sourceRef=src, targetRef=dst, associationDirection="None")
    add_diagram(root, model, layout, flow_ids)
    return root

def bounds(parent: ET.Element, box: Box) -> None:
    ET.SubElement(parent, q("dc", "Bounds"), {
        "x": str(round(box.x)), "y": str(round(box.y)), "width": str(round(box.w)), "height": str(round(box.h)),
    })

def add_diagram(root: ET.Element, model: Model, layout: Layout, flow_ids: dict[int, str]) -> None:
    diagram = ET.SubElement(root, q("bpmndi", "BPMNDiagram"), {"id": "BPMNDiagram_1"})
    plane = ET.SubElement(diagram, q("bpmndi", "BPMNPlane"), {"id": "BPMNPlane_1", "bpmnElement": "Collaboration_1"})
    for i, (_, box) in enumerate(layout.pools):
        shape = ET.SubElement(plane, q("bpmndi", "BPMNShape"), {
            "id": f"Participant_{i + 1}_di", "bpmnElement": f"Participant_{i + 1}", "isHorizontal": "true",
        })
        bounds(shape, box)
    for lane, box in layout.lanes.items():
        shape = ET.SubElement(plane, q("bpmndi", "BPMNShape"), {"id": f"{lane}_di", "bpmnElement": lane, "isHorizontal": "true"})
        bounds(shape, box)
    for node_id, box in layout.nodes.items():
        node = model.nodes[node_id]
        attrs = {"id": f"{node_id}_di", "bpmnElement": node_id}
        if node.kind == "subprocess":
            attrs["isExpanded"] = "false"
        if node.icon == "xor":
            attrs["isMarkerVisible"] = "true"
        shape = ET.SubElement(plane, q("bpmndi", "BPMNShape"), attrs)
        bounds(shape, box)
    for i, points in layout.edges.items():
        edge = ET.SubElement(plane, q("bpmndi", "BPMNEdge"), {"id": f"{flow_ids[i]}_di", "bpmnElement": flow_ids[i]})
        for x, y in points:
            ET.SubElement(edge, q("di", "waypoint"), {"x": str(round(x)), "y": str(round(y))})

def mmd_to_bpmn_xml(mmd: str) -> str:
    model, errors = parse(mmd)
    if errors:
        raise ValueError("; ".join(errors))
    root = build(model, compute(model))
    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"
