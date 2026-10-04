#!/usr/bin/env python3
"""把 dify/ 打成 .difypkg。

等价于官方 dify CLI 的 `dify plugin package ./dify`：
- 递归收录插件目录下所有文件（.difyignore 规则见下方 EXCLUDES）
- 剔除 difypkg 自身、.difyignore、_assets/logo.jpg、__pycache__/*.pyc
- 条目路径用 `/` 分隔、按路径排序（daemon 不要求显式目录条目）
- 时间戳固定为 1980-02-01，产物可字节级复现

用法：
  python scripts/package_dify_plugin.py [插件目录]     # 默认 <repo>/dify
  python scripts/package_dify_plugin.py dify --out x.difypkg
"""

from __future__ import annotations

import argparse
import os
import pathlib
import zipfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# 与 dify/.difyignore 保持一致：__pycache__/ *.pyc .git/ .DS_Store _assets/logo.jpg
SKIP_DIRS = {"__pycache__", ".git"}
SKIP_NAMES = {".difyignore", ".DS_Store"}
SKIP_RELATIVE = {pathlib.Path("_assets", "logo.jpg")}
STAMP = (1980, 2, 1, 0, 0, 0)


def package(plugin_dir: pathlib.Path, out: pathlib.Path) -> None:
    plugin_dir = plugin_dir.resolve()
    out = out.resolve()
    if not (plugin_dir / "manifest.yaml").exists():
        raise SystemExit(f"{plugin_dir}/manifest.yaml 不存在")

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(plugin_dir):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
            for name in sorted(files):
                full = pathlib.Path(root) / name
                rel = full.relative_to(plugin_dir)
                if name == out.name or name.endswith(".pyc") or name in SKIP_NAMES:
                    continue
                if rel in SKIP_RELATIVE:
                    continue
                info = zipfile.ZipInfo(rel.as_posix(), date_time=STAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                with z.open(info, "w") as dest:
                    dest.write(full.read_bytes())

    with zipfile.ZipFile(out) as z:
        bad = z.testzip()
        assert bad is None, f"zip 损坏: {bad}"
    print(f"打包完成: {out}")
    print(f"  {len(zipfile.ZipFile(out).namelist())} files, {out.stat().st_size} bytes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="打 .difypkg 包")
    parser.add_argument("plugin_dir", nargs="?", default=str(REPO_ROOT / "dify"))
    parser.add_argument(
        "--out",
        default=None,
        help="输出路径（默认 <插件目录>/hallucc.difypkg）",
    )
    args = parser.parse_args()
    plugin_dir = pathlib.Path(args.plugin_dir)
    out = pathlib.Path(args.out) if args.out else plugin_dir / "hallucc.difypkg"
    package(plugin_dir, out)
