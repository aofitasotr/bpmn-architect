import re
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.agents.graph import run
from app.bpmn.render import build_html

CSS = """
<style>
#MainMenu, footer, header [data-testid="stToolbar"] { visibility: hidden; }
.block-container { max-width: 1280px; padding-top: 2.5rem; }
h1 { font-weight: 600; letter-spacing: -0.02em; font-size: 1.6rem !important; }
.stButton > button, .stDownloadButton > button { border-radius: 10px; height: 2.6rem; }
textarea { border-radius: 10px !important; }
iframe { border: 1px solid #e5e7eb; border-radius: 12px; }
</style>
"""

def init() -> None:
    for key, value in {"request": "", "mmd": "", "errors": [], "redo_open": False}.items():
        st.session_state.setdefault(key, value)

def generate(request: str, previous: str = "", instruction: str = "") -> None:
    with st.spinner("Строю диаграмму…"):
        state = run(request, previous, instruction)
    st.session_state.request = request
    st.session_state.errors = state["errors"]
    st.session_state.mmd = state["mmd"] if not state["errors"] else ""
    st.session_state.redo_open = False

def reset() -> None:
    st.session_state.request = ""
    st.session_state.mmd = ""
    st.session_state.errors = []
    st.session_state.redo_open = False

def frame_height(mmd: str) -> int:
    lanes = len(re.findall(r"^\s*subgraph\b", mmd, re.M))
    return min(1400, max(420, lanes * 230 + 120))

def show_errors() -> None:
    if st.session_state.errors:
        st.error("Не удалось получить корректную диаграмму:\n\n" + "\n".join(f"- {e}" for e in st.session_state.errors))

def input_view() -> None:
    text = st.text_area(
        "Описание процесса",
        value=st.session_state.request,
        height=160,
        placeholder="Опишите бизнес-процесс: участники, шаги, условия, результат",
        label_visibility="collapsed",
    )
    if st.button("Создать", type="primary", disabled=not text.strip()):
        generate(text.strip())
        st.rerun()
    show_errors()
    if st.session_state.errors and st.session_state.request:
        if st.button("Пересоздать"):
            generate(st.session_state.request)
            st.rerun()

def result_view() -> None:
    mmd = st.session_state.mmd
    st.caption(st.session_state.request)
    st.iframe(build_html(mmd), height=frame_height(mmd))
    redo, again, download, new = st.columns(4)
    if redo.button("Переделать", use_container_width=True):
        st.session_state.redo_open = not st.session_state.redo_open
    if again.button("Пересоздать", use_container_width=True):
        generate(st.session_state.request)
        st.rerun()
    download.download_button(
        "Скачать",
        data=build_html(mmd),
        file_name="bpmn.html",
        mime="text/html",
        use_container_width=True,
    )
    if new.button("Новая диаграмма", use_container_width=True):
        reset()
        st.rerun()
    if st.session_state.redo_open:
        with st.form("redo_form", border=False):
            instruction = st.text_input(
                "Что переделать",
                placeholder="Например: добавь согласование с юристом после проверки заказа",
                label_visibility="collapsed",
            )
            if st.form_submit_button("Применить", type="primary") and instruction.strip():
                generate(st.session_state.request, mmd, instruction.strip())
                st.rerun()

def main() -> None:
    st.set_page_config(page_title="BPMN Architect", page_icon="◇", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    init()
    st.title("BPMN Architect")
    if st.session_state.mmd:
        result_view()
    else:
        input_view()

main()
