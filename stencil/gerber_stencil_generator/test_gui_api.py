from __future__ import annotations

import ast
import tkinter as tk
from pathlib import Path


def test_app_does_not_shadow_tk_internal_methods() -> None:
    source = Path(__file__).with_name("stencil_gui.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    app = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "StencilApp")
    methods = {node.name for node in app.body if isinstance(node, ast.FunctionDef)}
    collisions = (methods & set(dir(tk.Tk))) - {"__init__"}
    assert not collisions, f"Методы GUI конфликтуют с Tkinter: {sorted(collisions)}"
