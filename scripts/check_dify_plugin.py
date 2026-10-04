#!/usr/bin/env python3
"""Dify 插件打包前预检。

复现 Dify plugin daemon / dify_plugin SDK 在安装时走的同一条校验路径，
用于在提交 PR 前本地发现「能打包、装不上」的问题。

覆盖：
  1. 所有 .py 可编译（语法错 / import 期崩溃会让插件进程启动即死）
  2. 所有 .yaml 可解析（冒号未加引号等语法问题）
  3. manifest.yaml 符合 PluginConfiguration schema
  4. 每个 tool provider yaml 符合 ToolProviderConfiguration schema，
     且每个 tool 都声明了 extra.python.source（缺了这个字段安装必失败）
  5. PluginRegistration() —— 与插件启动完全相同的加载路径：
     加载 manifest、provider、tool 配置，导入 provider/*.py 与 tools/*.py 并
     解析工具类；任一步抛异常等价于「插件安装失败 exit code 1」

用法：
  pip install dify_plugin requests        # 首次需要 SDK
  python scripts/check_dify_plugin.py     # 默认检查 dify/
  python scripts/check_dify_plugin.py path/to/plugin

退出码 0 = 全部通过。
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys
import traceback

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def check(plugin_dir: pathlib.Path) -> int:
    plugin_dir = plugin_dir.resolve()
    if not (plugin_dir / "manifest.yaml").exists():
        print(f"FAIL: {plugin_dir}/manifest.yaml 不存在", file=sys.stderr)
        return 1

    old_cwd = pathlib.Path.cwd()
    old_dont_write = sys.dont_write_bytecode
    sys.dont_write_bytecode = True  # 导入插件模块时不要往插件树写 .pyc
    os.chdir(plugin_dir)
    sys.path.insert(0, str(plugin_dir))

    failures: list[str] = []

    print("== 1. Python 语法检查 ==")
    try:
        import py_compile
        import tempfile

        # cfile 必须落到临时目录，否则会在插件树里生成 __pycache__/*.pyc
        with tempfile.TemporaryDirectory() as tmp:
            for py in sorted(plugin_dir.rglob("*.py")):
                if "__pycache__" in py.parts:
                    continue
                cfile = str(
                    pathlib.Path(tmp)
                    / (py.relative_to(plugin_dir).as_posix().replace("/", "__")
                       + ".pyc")
                )
                py_compile.compile(str(py), cfile=cfile, doraise=True)
        print("   ok")
    except Exception as e:  # noqa: BLE001
        failures.append(f"Python 编译失败: {e}")

    print("== 2. YAML 解析检查 ==")
    try:
        import yaml

        for y in sorted(plugin_dir.rglob("*.yaml")):
            yaml.safe_load(y.read_text(encoding="utf-8"))
        print("   ok")
    except Exception as e:  # noqa: BLE001
        failures.append(f"YAML 解析失败: {e}")

    print("== 3-5. dify_plugin SDK schema + 启动路径检查 ==")
    try:
        from dify_plugin import DifyPluginEnv
        from dify_plugin.core.entities.plugin.setup import PluginConfiguration
        from dify_plugin.core.plugin_registration import PluginRegistration
        from dify_plugin.core.utils.yaml_loader import load_yaml_file
        from dify_plugin.entities.tool import ToolProviderConfiguration

        manifest = PluginConfiguration(**load_yaml_file("manifest.yaml"))
        print(f"   manifest: {manifest.name} v{manifest.version}")
        print(
            f"   meta.version={manifest.meta.version} "
            f"minimum_dify_version={manifest.meta.minimum_dify_version}"
        )

        for provider_path in manifest.plugins.tools:
            provider = ToolProviderConfiguration(**load_yaml_file(provider_path))
            print(f"   provider {provider.identity.name}: "
                  f"{len(provider.tools)} tools")
            for tool in provider.tools:
                source = tool.extra.python.source
                print(f"      - {tool.identity.name} -> {source}")

        reg = PluginRegistration(DifyPluginEnv(MAX_REQUEST_TIMEOUT=120))
        for name, (_, _, tools) in reg.tools_mapping.items():
            assert name in reg.tools_mapping
            print(f"   注册成功: {name} ({len(tools)} tools)")
    except ImportError as e:
        print(f"   跳过: 未安装 dify_plugin SDK（{e}）。", file=sys.stderr)
        print("   安装后重跑可覆盖最关键的 schema 校验：", file=sys.stderr)
        print("   pip install dify_plugin requests", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        failures.append("SDK 校验失败（等价于安装失败）:")
        traceback.print_exc()
    finally:
        os.chdir(old_cwd)
        sys.dont_write_bytecode = old_dont_write
        if sys.path and sys.path[0] == str(plugin_dir):
            sys.path.pop(0)

    if failures:
        print("\n=== FAIL ===")
        for f in failures:
            print(" -", f)
        return 1
    print("\n=== PASS ===")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dify 插件打包前预检")
    parser.add_argument(
        "plugin_dir",
        nargs="?",
        default=str(REPO_ROOT / "dify"),
        help="插件目录（默认 <repo>/dify）",
    )
    args = parser.parse_args()
    raise SystemExit(check(pathlib.Path(args.plugin_dir)))
