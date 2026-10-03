import json

from app.bpmn.validator import WEB

def build_html(mmd: str) -> str:
    html = (WEB / "index.html").read_text()
    icons = (WEB / "icons.json").read_text()
    payload = json.dumps(mmd, ensure_ascii=False).replace("</", "<\\/")
    return html.replace("__MMD__", payload).replace("__ICONS__", icons)
