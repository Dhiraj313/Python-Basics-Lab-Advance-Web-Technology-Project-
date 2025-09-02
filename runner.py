
import ast
import json
import sys
import tempfile
import subprocess
import textwrap
import os
from typing import Tuple, Dict, Any

FORBIDDEN_NAMES = {
    "open", "exec", "eval", "__import__", "compile", "input",
    "os", "sys", "subprocess", "shutil", "socket", "pathlib",
    "requests", "urllib", "ctypes", "multiprocessing"
}

FORBIDDEN_ATTRS = {"__class__", "__mro__", "__subclasses__", "__globals__", "__getattribute__", "__getattr__", "__dict__", "__call__", "__code__"}

def validate_ast(code: str) -> Tuple[bool, str]:
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return False, "Use of import is not allowed in this lab."
        if isinstance(node, ast.Attribute):
            if isinstance(node.attr, str) and (node.attr in FORBIDDEN_ATTRS or node.attr.startswith('__')):
                return False, "Access to dunder/private attributes is not allowed."
        if isinstance(node, ast.Name):
            if node.id in FORBIDDEN_NAMES:
                return False, f"Use of '{node.id}' is not allowed in this lab."
        if isinstance(node, ast.Call):
            # For extra safety, disallow exec/eval via call of Name
            if isinstance(node.func, ast.Name) and node.func.id in {"exec","eval"}:
                return False, "Use of exec/eval is not allowed."
    return True, ""

def _build_harness(code: str, tests: Dict[str, Any] | None) -> str:
    # Safe builtins: keep common learning primitives only
    safe_builtins = {
        "print": print, "range": range, "len": len, "int": int, "float": float,
        "str": str, "list": list, "dict": dict, "set": set, "tuple": tuple,
        "sum": sum, "min": min, "max": max, "abs": abs, "enumerate": enumerate, "zip": zip,
        "sorted": sorted, "round": round, "bool": bool
    }
    # We'll embed the student's code as a raw string literal
    harness = f'''
import io, sys, json, types
SAFE_BUILTINS = {{"print": print, "range": range, "len": len, "int": int, "float": float,
"str": str, "list": list, "dict": dict, "set": set, "tuple": tuple,
"sum": sum, "min": min, "max": max, "abs": abs, "enumerate": enumerate, "zip": zip,
"sorted": sorted, "round": round, "bool": bool}}

g = {{"__builtins__": SAFE_BUILTINS}}
stdout = io.StringIO()
sys.stdout = stdout

CODE = r\"\"\"{code}\"\"\"
result = {{"ok": True, "stdout": "", "tests": []}}
try:
    exec(compile(CODE, "<student>", "exec"), g, g)
except BaseException as e:
    result["ok"] = False
    result["error"] = f"{{type(e).__name__}}: {{e}}"

# Run tests if provided
tests = {json.dumps(tests) if tests else 'None'}
def run_tests():
    out = []
    passed = True
    if not tests:
        return True, out
    ttype = tests.get("type")
    if ttype == "stdout_exact":
        expected = tests.get("expected","").strip()
        actual = stdout.getvalue().strip()
        ok = (expected == actual)
        out.append({{"name": "stdout_exact", "expected": expected, "actual": actual, "pass": ok}})
        return ok, out
    if ttype == "function":
        fname = tests.get("name")
        cases = tests.get("cases", [])
        func = g.get(fname)
        if not callable(func):
            out.append({{"name": fname, "pass": False, "error": "Function not found or not callable."}})
            return False, out
        for i, c in enumerate(cases, 1):
            args = c.get("args", [])
            kwargs = c.get("kwargs", {})
            expect = c.get("expect")
            try:
                got = func(*args, **kwargs)
                ok = (got == expect)
                out.append({{"case": i, "args": args, "expect": expect, "actual": got, "pass": ok}})
                if not ok:
                    passed = False
            except BaseException as e:
                out.append({{"case": i, "args": args, "error": f"{{type(e).__name__)}}: {{e}}", "pass": False}})
                passed = False
        return passed, out
    # Unknown test type: treat as success, but record
    out.append({{"note": "No tests run"}})
    return True, out

try:
    tpass, details = run_tests()
    result["tests"] = details
    if result["ok"]:
        result["ok"] = tpass if tests else result["ok"]
except BaseException as e:
    result["ok"] = False
    result["error"] = f"Test harness error: {{type(e).__name__}}: {{e}}"

result["stdout"] = stdout.getvalue()
print(json.dumps(result))
'''
    return harness

def run_user_code(code: str, tests: Dict[str, Any] | None = None, timeout: int = 3) -> Dict[str, Any]:
    ok, msg = validate_ast(code)
    if not ok:
        return {"ok": False, "error": msg, "stdout": "", "tests": []}
    harness_code = _build_harness(code, tests)
    with tempfile.TemporaryDirectory() as td:
        harness_file = os.path.join(td, "harness.py")
        with open(harness_file, "w", encoding="utf-8") as f:
            f.write(harness_code)
        try:
            # Use -I (isolated), -B (no .pyc), -S (no site)
            proc = subprocess.run([sys.executable, "-I", "-B", "-S", harness_file],
                                  capture_output=True, text=True, timeout=timeout, cwd=td)
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "Execution timed out (limit 3s).", "stdout": "", "tests": []}
    if proc.returncode != 0:
        # Likely syntax error in harness (rare) or print from Python itself
        err = proc.stderr.strip() or proc.stdout.strip()
        return {"ok": False, "error": f"Runner error: {err[:500]}", "stdout": "", "tests": []}
    try:
        data = json.loads(proc.stdout.strip().splitlines()[-1])
        # Clamp very long outputs
        if isinstance(data.get("stdout"), str) and len(data["stdout"]) > 6000:
            data["stdout"] = data["stdout"][:6000] + "\n...[truncated]"
        return data
    except json.JSONDecodeError:
        return {"ok": False, "error": "Failed to decode runner output.", "stdout": proc.stdout, "tests": []}
