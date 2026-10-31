"""Exercise real GUI function bodies without opening a desktop or logging in."""
import ast
from pathlib import Path


def load_functions(names, namespace):
    tree = ast.parse((Path(__file__).resolve().parents[1] / 'YOTO.py').read_text())
    nodes = [node for node in tree.body
             if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'YOTO.py', 'exec'), namespace)
    return namespace
