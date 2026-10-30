#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WorkBuddy Experts Toolkit
=========================
程序化管理的专家信息工具，提供三类能力：

  1) export  将全部专家导出为 CSV / JSON（含 名字 / 职业 / 分类 / promptFile 路径）
  2) query   按「关键词 + 分类」组合查询（分类支持多值 AND / OR）
  3) show    按专家标识（id / plugin / agentName / 文件名）读取并展示提示词内容

设计原则：纯标准库、无第三方依赖；既可作为 CLI 调用，
也可 `import expert_tools` 后直接调用函数（见文件底部 API）。

用法示例：
  python expert_tools.py export
  python expert_tools.py query --category 金融投资 --keyword 腾讯云
  python expert_tools.py query --category 技术工程 游戏空间 --category-mode or
  python expert_tools.py show a-share-analysis
  python expert_tools.py show stock-partner-team
"""

import argparse
import csv
import json
import os
import sys

# --------------------------------------------------------------------------- #
# 路径解析
# --------------------------------------------------------------------------- #
def find_repo_root(start=None):
    """向上查找包含 experts/manifest.json 的目录作为仓库根。"""
    cur = os.path.abspath(start or os.path.dirname(os.path.abspath(__file__)))
    # 也尝试从当前工作目录向上找
    candidates = [cur, os.getcwd()]
    for base in candidates:
        d = base
        while True:
            if os.path.isfile(os.path.join(d, "experts", "manifest.json")):
                return d
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
    raise FileNotFoundError("未找到 experts/manifest.json，请确认在仓库根目录运行。")


# --------------------------------------------------------------------------- #
# 数据加载与规整
# --------------------------------------------------------------------------- #
def load_manifest(repo_root=None):
    repo_root = repo_root or find_repo_root()
    manifest_path = os.path.join(repo_root, "experts", "manifest.json")
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    # 分类映射: categoryId -> {zh, en, description}
    cat_map = {}
    for c in manifest.get("categories", []):
        name = c.get("name", {})
        cat_map[c.get("id")] = {
            "id": c.get("id"),
            "zh": name.get("zh", ""),
            "en": name.get("en", ""),
        }
    return manifest, cat_map, repo_root


def _text(d, lang="zh"):
    """从 {zh,en} 或纯字符串中取文本。"""
    if isinstance(d, dict):
        return d.get(lang) or d.get("zh") or d.get("en") or ""
    return d or ""


def build_records(repo_root=None):
    """将 manifest 规整为扁平记录列表。"""
    manifest, cat_map, repo_root = load_manifest(repo_root)
    records = []
    for e in manifest.get("experts", []):
        cid = e.get("categoryId", "")
        cat = cat_map.get(cid, {"id": cid, "zh": "", "en": ""})

        # 提示词路径：优先用 promptFile，缺失时按 plugin/agentName 兜底推导
        pf = e.get("promptFile") or ""
        if not pf:
            plugin = e.get("plugin")
            agent = e.get("agentName")
            if plugin and agent:
                pf = "/plugins/%s/agents/%s.md" % (plugin, agent)

        # 磁盘相对路径： experts/prompts + promptFile（统一用正斜杠，便于程序解析）
        disk_path = ""
        prompt_exists = False
        if pf:
            rel = pf.lstrip("/").replace("\\", "/")
            disk_path = "experts/prompts/" + rel
            prompt_exists = os.path.isfile(os.path.join(repo_root, *disk_path.split("/")))

        tags = e.get("tags", []) or []
        tags_zh = " / ".join(_text(t, "zh") for t in tags)
        tags_en = " / ".join(_text(t, "en") for t in tags)

        records.append({
            "id": e.get("id", ""),
            "name_zh": _text(e.get("displayName"), "zh"),
            "name_en": _text(e.get("displayName"), "en"),
            "profession_zh": _text(e.get("profession"), "zh"),
            "profession_en": _text(e.get("profession"), "en"),
            "category_id": cid,
            "category_zh": cat.get("zh", ""),
            "category_en": cat.get("en", ""),
            "plugin": e.get("plugin", ""),
            "agentName": e.get("agentName", ""),
            "expertType": e.get("expertType", ""),
            "promptFile": pf,
            "prompt_path": disk_path,
            "prompt_exists": prompt_exists,
            "tags_zh": tags_zh,
            "tags_en": tags_en,
            "description_zh": _text(e.get("description"), "zh"),
        })
    return records


# --------------------------------------------------------------------------- #
# 导出
# --------------------------------------------------------------------------- #
EXPORT_FIELDS = [
    ("id", "id"),
    ("name_zh", "名字(中文)"),
    ("name_en", "名字(英文)"),
    ("profession_zh", "职业(中文)"),
    ("profession_en", "职业(英文)"),
    ("category_zh", "分类(中文)"),
    ("category_en", "分类(英文)"),
    ("category_id", "分类ID"),
    ("plugin", "插件目录"),
    ("agentName", "Agent名"),
    ("tags_zh", "标签(中文)"),
    ("promptFile", "promptFile路径"),
    ("prompt_path", "磁盘相对路径"),
]


def export_csv(records, out_path):
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow([h for _, h in EXPORT_FIELDS])
        for r in records:
            w.writerow([r.get(k, "") for k, _ in EXPORT_FIELDS])


def export_json(records, out_path):
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def cmd_export(args):
    records = build_records()
    repo_root = find_repo_root()
    csv_path = os.path.join(repo_root, "toolkit", "experts.csv")
    json_path = os.path.join(repo_root, "toolkit", "experts.json")
    export_csv(records, csv_path)
    export_json(records, json_path)
    missing = [r["id"] for r in records if not r["prompt_exists"]]
    print("导出完成：")
    print("  记录数        : %d" % len(records))
    print("  CSV  -> %s" % csv_path)
    print("  JSON -> %s" % json_path)
    if missing:
        print("  警告：以下专家提示词文件未在磁盘找到：%s" % ", ".join(missing))
    else:
        print("  完整性：全部 %d 位专家的提示词文件均存在。" % len(records))


# --------------------------------------------------------------------------- #
# 查询
# --------------------------------------------------------------------------- #
def _match_category(rec, cats):
    """rec 的分类是否与给定分类集合匹配（任一即可）。"""
    rec_cats = {rec["category_zh"], rec["category_en"], rec["category_id"]}
    # 模糊：用户可能输入部分中文名
    for c in cats:
        c = c.strip()
        if not c:
            continue
        for rc in rec_cats:
            if rc and (rc == c or c in rc or rc in c):
                return True
    return False


def query_records(records, categories=None, keyword=None, category_mode="or"):
    cats = [c for c in (categories or []) if c.strip()]
    kw = (keyword or "").strip().lower()
    result = []
    for r in records:
        # 分类过滤
        if cats:
            matched = _match_category(r, cats)
            if category_mode == "and":
                # 要求匹配每一个给定分类（单分类专家通常只能命中一个，
                # 多分类同时命中返回空，符合“同时属于”语义）
                matched = all(
                    any(c in rc or rc in c
                        for rc in {r["category_zh"], r["category_en"], r["category_id"]})
                    for c in cats if c
                )
            if not matched:
                continue
        # 关键词过滤（名字/职业/标签/描述/插件/id）
        if kw:
            hay = " ".join([
                r["name_zh"], r["name_en"], r["profession_zh"], r["profession_en"],
                r["tags_zh"], r["tags_en"], r["description_zh"], r["plugin"],
                r["id"], r["agentName"],
            ]).lower()
            if kw not in hay:
                continue
        result.append(r)
    return result


def cmd_query(args):
    records = build_records()
    result = query_records(
        records,
        categories=args.category,
        keyword=args.keyword,
        category_mode=args.category_mode,
    )
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if not result:
            print("（无匹配结果）")
            return
        hdr = "%-22s %-14s %-8s %s" % ("id", "分类", "插件", "名字")
        print(hdr)
        print("-" * len(hdr))
        for r in result:
            print("%-22s %-14s %-8s %s" % (
                r["id"][:22], r["category_zh"][:14], r["plugin"][:8], r["name_zh"]))
        print("\n共 %d 条" % len(result))


# --------------------------------------------------------------------------- #
# 展示提示词内容
# --------------------------------------------------------------------------- #
def resolve_experts(records, token):
    """按 id / plugin / agentName / promptFile 基名 解析专家记录。"""
    token_l = token.lower()
    exact = []
    plugin_hits = []
    for r in records:
        if token_l == r["id"].lower():
            exact.append(r)
        if token_l == r["plugin"].lower() or token_l == r["agentName"].lower():
            plugin_hits.append(r)
    if exact:
        return exact
    if plugin_hits:
        return plugin_hits
    # 再尝试 promptFile 基名或包含匹配
    fuzzy = [r for r in records
             if token_l in r["promptFile"].lower() or token_l in r["id"].lower()]
    return fuzzy


def cmd_show(args):
    records = build_records()
    repo_root = find_repo_root()
    matched = resolve_experts(records, args.token)
    if not matched:
        print("未找到匹配专家：%s" % args.token, file=sys.stderr)
        sys.exit(1)

    shown = 0
    for r in matched:
        pf = r["prompt_path"]
        full = os.path.join(repo_root, pf) if pf else ""
        print("=" * 72)
        print("专家 ID     : %s" % r["id"])
        print("名字         : %s (%s)" % (r["name_zh"], r["name_en"]))
        print("职业         : %s" % r["profession_zh"])
        print("分类         : %s / %s" % (r["category_zh"], r["category_en"]))
        print("插件目录     : %s" % r["plugin"])
        print("prompt 文件  : %s" % pf)
        print("=" * 72)
        if full and os.path.isfile(full):
            with open(full, encoding="utf-8") as f:
                print(f.read())
            shown += 1
        else:
            print("（提示词文件不存在：%s）" % full)
    print("\n已展示 %d 个专家。" % shown)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser():
    p = argparse.ArgumentParser(description="WorkBuddy 专家信息管理工具")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("export", help="导出全部专家为 CSV 与 JSON")

    q = sub.add_parser("query", help="按分类/关键词组合查询")
    q.add_argument("--category", nargs="+", default=[], help="分类名/ID，可多个")
    q.add_argument("--keyword", default="", help="关键词（名字/职业/标签/描述）")
    q.add_argument("--category-mode", choices=["or", "and"], default="or",
                   help="多分类时的匹配模式：or=任一, and=同时(交集)")
    q.add_argument("--format", choices=["json", "table"], default="json",
                   help="输出格式，默认 json（便于程序调用）")

    s = sub.add_parser("show", help="按标识读取并展示提示词内容")
    s.add_argument("token", help="专家 id / plugin / agentName / 文件名")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.cmd == "export":
        cmd_export(args)
    elif args.cmd == "query":
        cmd_query(args)
    elif args.cmd == "show":
        cmd_show(args)


# --------------------------------------------------------------------------- #
# 程序化调用 API（直接 import 使用）
# --------------------------------------------------------------------------- #
__all__ = [
    "find_repo_root", "load_manifest", "build_records",
    "export_csv", "export_json", "query_records", "resolve_experts",
]


if __name__ == "__main__":
    main()
