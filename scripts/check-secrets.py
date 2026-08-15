#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kic-ai-cn 安全扫描器（Qoder/CodeSec 风格，读取 security-patterns.yaml）
用法:
  python scripts/check-secrets.py            # 扫所有 git 跟踪的文件
  python scripts/check-secrets.py --staged   # 只扫暂存区文件（pre-commit 钩子用）
命中任何规则 → 退出码 1，否则 0
"""
import fnmatch
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_FILE = os.path.join(ROOT, "security-patterns.yaml")

# 永远跳过（与 Qoder file_filter 对齐）
ALWAYS_EXCLUDE = [
    "node_modules/", "dist/", "lib/", "build/", ".next/", ".git/",
    "__pycache__/", ".venv/", "target/", "vendor/",
]
ALWAYS_EXCLUDE_EXTS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".pdf", ".zip",
    ".tar", ".gz", ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".mp3",
    ".lock", ".min.js",
}


def unescape_yaml_double_quoted(s: str) -> str:
    """极简 YAML 双引号字符串转义处理（只处理我们用到的那几个）。"""
    return s.replace("\\", "\x00").replace('\"', '"').replace("\n", "\n").replace("\x00", "\\")


def parse_rules(text: str):
    """极简 YAML 子集解析：- ruleName: ... / 子字段（不依赖 PyYAML）。"""
    rules = []
    cur = None
    field = None  # 当前正在收集的列表字段
    for raw in text.splitlines():
        line = raw.rstrip()
        s = line.strip()
        if s.startswith("- ruleName:"):
            if cur:
                rules.append(cur)
            cur = {
                "ruleName": s.split(":", 1)[1].strip().strip("'\""),
                "substrings": [], "regex": None, "severity": "MEDIUM",
                "paths": [], "exclude_paths": [], "path_glob": None,
                "reminder": "",
            }
            field = None
        elif cur is not None:
            if s.startswith("substrings:"):
                field = "substrings"
            elif s.startswith("regex:"):
                field = None
                v = s.split(":", 1)[1].strip()
                if v.startswith('"') and v.endswith('"'):
                    cur["regex"] = unescape_yaml_double_quoted(v[1:-1])
                else:
                    cur["regex"] = v.strip("'")
            elif s.startswith("severity:"):
                cur["severity"] = s.split(":", 1)[1].strip()
            elif s.startswith("paths:"):
                field = "paths"
            elif s.startswith("exclude_paths:"):
                field = "exclude_paths"
            elif s.startswith("path_glob:"):
                field = None
                cur["path_glob"] = s.split(":", 1)[1].strip().strip("'\"")
            elif s.startswith("reminder:"):
                field = None
                cur["reminder"] = s.split(":", 1)[1].strip().strip("'\"")
            elif field and s.startswith("- "):
                cur[field].append(s[2:].strip().strip("'\""))
    if cur:
        rules.append(cur)
    return rules


def should_skip(path: str) -> bool:
    norm = path.replace("\\", "/")
    for p in ALWAYS_EXCLUDE:
        if p in norm:
            return True
    if any(norm.endswith(ext) for ext in ALWAYS_EXCLUDE_EXTS):
        return True
    return False


def rule_path_allowed(rule, path: str) -> bool:
    norm = path.replace("\\", "/")
    if rule["paths"] and not any(norm.startswith(p.rstrip("/") + "/") or norm == p.rstrip("/") for p in rule["paths"]):
        return False
    if rule["exclude_paths"] and any(norm.startswith(p.rstrip("/") + "/") or norm == p.rstrip("/") for p in rule["exclude_paths"]):
        return False
    if rule["path_glob"] and not fnmatch.fnmatch(norm, rule["path_glob"]):
        return False
    return True


def scan_file(path: str, rules):
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return []
    try:
        content = data.decode("utf-8")
    except UnicodeDecodeError:
        content = data.decode("utf-8", errors="replace")
    lines = content.splitlines()
    hits = []
    for rule in rules:
        if not rule_path_allowed(rule, path):
            continue
        if rule["regex"]:
            try:
                rx = re.compile(rule["regex"])
            except re.error:
                continue  # 坏规则跳过（与 Qoder 一致）
            m = rx.search(content)
            if m:
                lineno = content[: m.start()].count("\n") + 1
                hits.append((lineno, rule))
        else:
            for sub in rule["substrings"]:
                if sub in content:
                    idx = content.find(sub)
                    lineno = content[:idx].count("\n") + 1
                    hits.append((lineno, rule))
                    break
    return hits


def main():
    staged = "--staged" in sys.argv
    if staged:
        out = subprocess.run(["git", "diff", "--cached", "--name-only"],
                             capture_output=True, text=True, cwd=ROOT).stdout
    else:
        out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, cwd=ROOT).stdout
    files = [f for f in out.splitlines() if not should_skip(f)]

    with open(RULES_FILE, encoding="utf-8") as f:
        rules = parse_rules(f.read())
    if not rules:
        print("✋ 规则文件为空或解析失败，请检查 security-patterns.yaml")
        return 2

    total = 0
    for path in files:
        abs_path = os.path.join(ROOT, path.replace("/", os.sep))
        for lineno, rule in scan_file(abs_path, rules):
            total += 1
            print(f"✋ {path}:{lineno}  [{rule['severity']}] {rule['ruleName']}")
            if rule["reminder"]:
                print(f"   提示: {rule['reminder']}")
    if total:
        print(f"\n共发现 {total} 处问题，已阻止！请修复后重试。")
        return 1
    print("✓ 安全扫描通过：未检测到密钥/危险模式")
    return 0


if __name__ == "__main__":
    sys.exit(main())
