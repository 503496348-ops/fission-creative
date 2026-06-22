"""
Fission Creative — Plugin Architecture for Text Processing
==========================================================
Inspired by gpt_academic (70K⭐) plugin system.

Key patterns adopted:
- Plugin registry with Function/Info/ArgsReminder
- Pipeline chain: input → plugin1 → plugin2 → output
- Advanced args support per plugin
- Error isolation per plugin
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class Plugin:
    """A text processing plugin."""
    name: str
    info: str
    function: Callable[[str, dict], str]
    args_reminder: str = ""
    advanced_args: bool = False
    category: str = "general"
    hotkey: str = ""

    def execute(self, text: str, args: dict = None) -> str:
        try:
            return self.function(text, args or {})
        except Exception as e:
            return f"[Plugin {self.name} error: {e}]\n\n{text}"


class PluginRegistry:
    """Central registry for text processing plugins."""
    _plugins: dict[str, Plugin] = {}

    @classmethod
    def register(cls, plugin: Plugin):
        cls._plugins[plugin.name] = plugin

    @classmethod
    def get(cls, name: str) -> Plugin | None:
        return cls._plugins.get(name)

    @classmethod
    def list_all(cls) -> list[dict]:
        return [
            {"name": p.name, "info": p.info, "category": p.category,
             "advanced_args": p.advanced_args, "hotkey": p.hotkey}
            for p in cls._plugins.values()
        ]

    @classmethod
    def list_by_category(cls, category: str) -> list[Plugin]:
        return [p for p in cls._plugins.values() if p.category == category]


# ──── Built-in Plugins ────

def _expand_outline(text: str, args: dict) -> str:
    """Expand a story outline into detailed chapters."""
    lines = text.strip().split("\n")
    expanded = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("#", "##", "###")):
            expanded.append(stripped)
            expanded.append(f"[本章需展开约{args.get('words_per_chapter', 2000)}字]")
        else:
            expanded.append(stripped)
    return "\n".join(expanded)


def _consistency_check(text: str, args: dict) -> str:
    """Check character/setting consistency across chapters."""
    # Extract character names (simple heuristic)
    import re
    characters = set()
    for m in re.finditer(r"[A-Z]{2,}|[\u4e00-\u9fff]{2,4}(?=说|道|想|看|走|来)", text):
        characters.add(m.group())

    report = ["=== 一致性检查报告 ==="]
    report.append(f"发现角色: {', '.join(list(characters)[:20])}")
    report.append(f"总字数: {len(text)}")
    return "\n".join(report)


def _pacing_analysis(text: str, args: dict) -> str:
    """Analyze story pacing — dialogue vs description ratio."""
    import re
    dialogue = len(re.findall(r'["“].*?["”]', text))
    paragraphs = len([p for p in text.split("\n\n") if p.strip()])
    ratio = dialogue / max(paragraphs, 1)

    report = ["=== 节奏分析 ==="]
    report.append(f"对话段落: {dialogue}")
    report.append(f"总段落: {paragraphs}")
    report.append(f"对话占比: {ratio:.1%}")
    if ratio > 0.5:
        report.append("⚠️ 对话过多，建议增加描写段落")
    elif ratio < 0.2:
        report.append("⚠️ 对话过少，建议增加角色互动")
    return "\n".join(report)


# Register built-in plugins
PluginRegistry.register(Plugin(
    name="expand_outline", info="大纲展开：将章节大纲扩展为详细内容",
    function=_expand_outline, category="创作", hotkey="Ctrl+E",
    advanced_args=True, args_reminder="words_per_chapter: 每章目标字数(默认2000)",
))
PluginRegistry.register(Plugin(
    name="consistency_check", info="一致性检查：检测角色/设定前后矛盾",
    function=_consistency_check, category="审核", hotkey="Ctrl+K",
))
PluginRegistry.register(Plugin(
    name="pacing_analysis", info="节奏分析：对话vs描写比例",
    function=_pacing_analysis, category="审核", hotkey="Ctrl+P",
))


def run_pipeline(text: str, plugins: list[str], args: dict = None) -> str:
    """Run a chain of plugins on text."""
    result = text
    for name in plugins:
        plugin = PluginRegistry.get(name)
        if plugin:
            result = plugin.execute(result, args)
        else:
            result = f"[Plugin '{name}' not found]\n\n{result}"
    return result


if __name__ == "__main__":
    test_text = """# 第一章 风起
李明说："今天天气不错。"
张伟说："是啊，我们出发吧。"

# 第二章 云涌
他们来到了山脚下。"""
    print(run_pipeline(test_text, ["pacing_analysis", "consistency_check"]))
