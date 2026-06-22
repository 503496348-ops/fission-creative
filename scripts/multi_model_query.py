"""
Fission Creative — Multi-Model Parallel Query Engine
=====================================================
Inspired by gpt_academic (70K⭐) multi-model parallel querying.

Key capabilities:
- Query multiple LLM providers simultaneously (OpenAI, Anthropic, local, etc.)
- Aggregate & compare creative outputs across models
- Best-pick selection for story generation tasks
- Streaming support with per-model timeout control
- Integrates with plugin_architecture.py PluginRegistry

Brand: AtomCollide-智械工坊
License: GPL v3
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

import aiohttp


# ──── Model Provider Definitions ────

class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    LOCAL = "local"  # Ollama / LM Studio / any OpenAI-compatible local endpoint


@dataclass
class ModelConfig:
    """Configuration for a single LLM endpoint."""
    name: str
    provider: ModelProvider
    base_url: str
    api_key: str = ""
    model_id: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 120
    priority: int = 0  # higher = preferred when picking best result

    def __post_init__(self):
        if not self.model_id:
            defaults = {
                ModelProvider.OPENAI: "gpt-4o",
                ModelProvider.ANTHROPIC: "claude-sonnet-4-20250514",
                ModelProvider.DEEPSEEK: "deepseek-chat",
                ModelProvider.QWEN: "qwen-max",
                ModelProvider.LOCAL: "llama3",
            }
            self.model_id = defaults.get(self.provider, "gpt-4o")


@dataclass
class QueryResult:
    """Result from a single model query."""
    model_name: str
    provider: str
    content: str
    latency_ms: float = 0.0
    token_count: int = 0
    error: Optional[str] = None
    raw_response: dict = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.error is None and bool(self.content)


# ──── API Callers (per-provider) ────

async def _call_openai_compatible(
    session: aiohttp.ClientSession,
    config: ModelConfig,
    system_prompt: str,
    user_prompt: str,
) -> QueryResult:
    """Call any OpenAI-compatible API (OpenAI, DeepSeek, Qwen, local)."""
    url = f"{config.base_url.rstrip('/')}/chat/completions"
    headers = {"Content-Type": "application/json"}
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"

    payload = {
        "model": config.model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": config.max_tokens,
        "temperature": config.temperature,
    }

    start = time.monotonic()
    try:
        async with session.post(
            url, json=payload, headers=headers,
            timeout=aiohttp.ClientTimeout(total=config.timeout),
        ) as resp:
            data = await resp.json()
            latency = (time.monotonic() - start) * 1000

            if resp.status != 200:
                error_msg = data.get("error", {}).get("message", f"HTTP {resp.status}")
                return QueryResult(
                    model_name=config.name, provider=config.provider.value,
                    content="", latency_ms=latency, error=error_msg, raw_response=data,
                )

            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return QueryResult(
                model_name=config.name, provider=config.provider.value,
                content=content, latency_ms=latency,
                token_count=usage.get("total_tokens", 0),
                raw_response=data,
            )
    except asyncio.TimeoutError:
        return QueryResult(
            model_name=config.name, provider=config.provider.value,
            content="", error=f"Timeout after {config.timeout}s",
        )
    except Exception as e:
        return QueryResult(
            model_name=config.name, provider=config.provider.value,
            content="", error=str(e),
        )


async def _call_anthropic(
    session: aiohttp.ClientSession,
    config: ModelConfig,
    system_prompt: str,
    user_prompt: str,
) -> QueryResult:
    """Call Anthropic Claude API."""
    url = f"{config.base_url.rstrip('/')}/v1/messages"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": config.api_key,
        "anthropic-version": "2023-06-01",
    }
    payload = {
        "model": config.model_id,
        "max_tokens": config.max_tokens,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
        "temperature": config.temperature,
    }

    start = time.monotonic()
    try:
        async with session.post(
            url, json=payload, headers=headers,
            timeout=aiohttp.ClientTimeout(total=config.timeout),
        ) as resp:
            data = await resp.json()
            latency = (time.monotonic() - start) * 1000

            if resp.status != 200:
                error_msg = data.get("error", {}).get("message", f"HTTP {resp.status}")
                return QueryResult(
                    model_name=config.name, provider=config.provider.value,
                    content="", latency_ms=latency, error=error_msg, raw_response=data,
                )

            content = data["content"][0]["text"]
            usage = data.get("usage", {})
            return QueryResult(
                model_name=config.name, provider=config.provider.value,
                content=content, latency_ms=latency,
                token_count=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                raw_response=data,
            )
    except asyncio.TimeoutError:
        return QueryResult(
            model_name=config.name, provider=config.provider.value,
            content="", error=f"Timeout after {config.timeout}s",
        )
    except Exception as e:
        return QueryResult(
            model_name=config.name, provider=config.provider.value,
            content="", error=str(e),
        )


# Provider dispatch
_PROVIDER_CALLERS: dict[ModelProvider, Callable] = {
    ModelProvider.OPENAI: _call_openai_compatible,
    ModelProvider.DEEPSEEK: _call_openai_compatible,
    ModelProvider.QWEN: _call_openai_compatible,
    ModelProvider.LOCAL: _call_openai_compatible,
    ModelProvider.ANTHROPIC: _call_anthropic,
}


# ──── Multi-Model Query Engine ────

class MultiModelQueryEngine:
    """
    Query multiple LLMs in parallel and compare results.

    Usage:
        engine = MultiModelQueryEngine(configs)
        results = await engine.query_parallel(system_prompt, user_prompt)
        best = engine.pick_best(results, strategy="longest")
    """

    def __init__(self, configs: list[ModelConfig] | None = None):
        self.configs: list[ModelConfig] = configs or []
        self._history: list[dict] = []

    @classmethod
    def from_env(cls) -> "MultiModelQueryEngine":
        """Build engine from environment variables.

        Supported env vars:
            MULTI_MODEL_CONFIGS  — JSON array of model configs, e.g.
                [{"name":"gpt4o","provider":"openai","base_url":"https://api.openai.com/v1",
                  "api_key":"sk-...","model_id":"gpt-4o"},
                 {"name":"deepseek","provider":"deepseek","base_url":"https://api.deepseek.com/v1",
                  "api_key":"sk-...","model_id":"deepseek-chat"}]
        """
        raw = os.environ.get("MULTI_MODEL_CONFIGS", "")
        if not raw:
            # Fallback: try individual keys
            configs = []
            if os.environ.get("OPENAI_API_KEY"):
                configs.append(ModelConfig(
                    name="openai", provider=ModelProvider.OPENAI,
                    base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                    api_key=os.environ["OPENAI_API_KEY"],
                ))
            if os.environ.get("DEEPSEEK_API_KEY"):
                configs.append(ModelConfig(
                    name="deepseek", provider=ModelProvider.DEEPSEEK,
                    base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
                    api_key=os.environ["DEEPSEEK_API_KEY"],
                ))
            return cls(configs)

        items = json.loads(raw)
        configs = []
        for item in items:
            provider = ModelProvider(item.get("provider", "openai"))
            configs.append(ModelConfig(
                name=item.get("name", provider.value),
                provider=provider,
                base_url=item.get("base_url", ""),
                api_key=item.get("api_key", ""),
                model_id=item.get("model_id", ""),
                max_tokens=item.get("max_tokens", 4096),
                temperature=item.get("temperature", 0.7),
                timeout=item.get("timeout", 120),
                priority=item.get("priority", 0),
            ))
        return cls(configs)

    def add_config(self, config: ModelConfig):
        """Add a model configuration at runtime."""
        self.configs.append(config)

    async def query_parallel(
        self,
        system_prompt: str,
        user_prompt: str,
        models: list[str] | None = None,
    ) -> list[QueryResult]:
        """Query all configured models (or a subset) in parallel."""
        targets = self.configs
        if models:
            targets = [c for c in self.configs if c.name in models]

        if not targets:
            return [QueryResult(
                model_name="none", provider="none", content="",
                error="No models configured",
            )]

        async with aiohttp.ClientSession() as session:
            tasks = []
            for cfg in targets:
                caller = _PROVIDER_CALLERS.get(cfg.provider, _call_openai_compatible)
                tasks.append(caller(session, cfg, system_prompt, user_prompt))

            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to QueryResult errors
        final: list[QueryResult] = []
        for i, r in enumerate(results):
            if isinstance(r, BaseException):
                final.append(QueryResult(
                    model_name=targets[i].name, provider=targets[i].provider.value,
                    content="", error=str(r),
                ))
            elif isinstance(r, QueryResult):
                final.append(r)
            else:
                final.append(QueryResult(
                    model_name=targets[i].name, provider=targets[i].provider.value,
                    content="", error=f"Unexpected result type: {type(r)}",
                ))

        # Record history
        self._history.append({
            "timestamp": time.time(),
            "system_prompt": system_prompt[:200],
            "user_prompt": user_prompt[:200],
            "results": [
                {"model": r.model_name, "success": r.success,
                 "latency_ms": r.latency_ms, "error": r.error}
                for r in final
            ],
        })
        return final

    def pick_best(
        self,
        results: list[QueryResult],
        strategy: str = "priority",
    ) -> QueryResult | None:
        """Pick the best result from parallel queries.

        Strategies:
            "priority" — highest config.priority among successes
            "fastest"  — lowest latency
            "longest"  — longest content (for creative writing, more is often better)
            "first"    — first successful result
        """
        successful = [r for r in results if r.success]
        if not successful:
            return None

        if strategy == "fastest":
            return min(successful, key=lambda r: r.latency_ms)
        elif strategy == "longest":
            return max(successful, key=lambda r: len(r.content))
        elif strategy == "first":
            return successful[0]
        else:  # priority
            # Map model names back to config priorities
            priority_map = {c.name: c.priority for c in self.configs}
            return max(successful, key=lambda r: priority_map.get(r.model_name, 0))

    def format_comparison(self, results: list[QueryResult]) -> str:
        """Format results side by side for human comparison."""
        lines = ["# 多模型对比结果\n"]
        for i, r in enumerate(results, 1):
            status = "✅" if r.success else "❌"
            lines.append(f"## {status} 模型 {i}: {r.model_name} ({r.provider})")
            lines.append(f"- 延迟: {r.latency_ms:.0f}ms")
            if r.token_count:
                lines.append(f"- Token数: {r.token_count}")
            if r.error:
                lines.append(f"- 错误: {r.error}")
            lines.append(f"\n### 输出内容\n{r.content[:3000]}")
            if len(r.content) > 3000:
                lines.append(f"\n... (共{len(r.content)}字)")
            lines.append("\n---\n")
        return "\n".join(lines)

    @property
    def history(self) -> list[dict]:
        return list(self._history)


# ──── Convenience Functions ────

def query_models(
    system_prompt: str,
    user_prompt: str,
    configs: list[ModelConfig] | None = None,
    pick: str = "priority",
) -> tuple[list[QueryResult], QueryResult | None]:
    """Synchronous convenience wrapper.

    Returns (all_results, best_result).
    """
    engine = MultiModelQueryEngine(configs or MultiModelQueryEngine.from_env().configs)
    results = asyncio.run(engine.query_parallel(system_prompt, user_prompt))
    best = engine.pick_best(results, strategy=pick)
    return results, best


# ──── Plugin Integration ────

def _multi_model_compare(text: str, args: dict) -> str:
    """Plugin: compare creative outputs across multiple models."""
    system_prompt = args.get("system_prompt", "你是一位资深网文编辑。请对以下内容进行评价和优化建议。")
    strategy = args.get("strategy", "priority")
    model_names = args.get("models", None)  # None = all configured

    engine = MultiModelQueryEngine.from_env()
    if not engine.configs:
        return "⚠️ 未配置多模型环境变量 (MULTI_MODEL_CONFIGS)。请参阅文档配置。"

    results = asyncio.run(engine.query_parallel(system_prompt, text, models=model_names))
    return engine.format_comparison(results)


def _multi_model_best(text: str, args: dict) -> str:
    """Plugin: query multiple models and return the best creative output."""
    system_prompt = args.get("system_prompt", "你是一位顶尖网文作家。请根据以下大纲/提示创作内容。")
    strategy = args.get("strategy", "longest")
    model_names = args.get("models", None)

    engine = MultiModelQueryEngine.from_env()
    if not engine.configs:
        return "⚠️ 未配置多模型环境变量 (MULTI_MODEL_CONFIGS)。请参阅文档配置。"

    results = asyncio.run(engine.query_parallel(system_prompt, text, models=model_names))
    best = engine.pick_best(results, strategy=strategy)

    if best:
        return f"## 最佳结果（策略: {strategy}，模型: {best.model_name}）\n\n{best.content}"
    else:
        errors = [f"- {r.model_name}: {r.error}" for r in results if r.error]
        return f"⚠️ 所有模型查询失败:\n" + "\n".join(errors)


# Register plugins (guarded import — only register if PluginRegistry exists)
try:
    from plugin_architecture import PluginRegistry, Plugin

    PluginRegistry.register(Plugin(
        name="multi_model_compare",
        info="多模型对比：同时查询多个LLM，对比创意输出",
        function=_multi_model_compare,
        category="创作",
        hotkey="Ctrl+M",
        advanced_args=True,
        args_reminder=(
            "system_prompt: 系统提示词; "
            "strategy: 选择策略(priority/fastest/longest/first); "
            "models: 模型名称列表(逗号分隔)"
        ),
    ))
    PluginRegistry.register(Plugin(
        name="multi_model_best",
        info="多模型优选：查询多个LLM，返回最佳创意输出",
        function=_multi_model_best,
        category="创作",
        hotkey="Ctrl+B",
        advanced_args=True,
        args_reminder=(
            "system_prompt: 系统提示词; "
            "strategy: 选择策略(priority/fastest/longest/first); "
            "models: 模型名称列表(逗号分隔)"
        ),
    ))
except ImportError:
    pass  # Standalone usage


# ──── CLI ────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python multi_model_query.py <prompt> [--system SYSTEM_PROMPT] [--strategy STRATEGY]")
        print("  Strategies: priority, fastest, longest, first")
        print("\nEnvironment variables:")
        print("  MULTI_MODEL_CONFIGS: JSON array of model configs")
        print("  OPENAI_API_KEY / DEEPSEEK_API_KEY: fallback single-model keys")
        sys.exit(1)

    prompt = sys.argv[1]
    system = "你是一位顶尖网文作家。请根据以下提示创作内容。"
    strategy = "longest"

    if "--system" in sys.argv:
        idx = sys.argv.index("--system")
        system = sys.argv[idx + 1]
    if "--strategy" in sys.argv:
        idx = sys.argv.index("--strategy")
        strategy = sys.argv[idx + 1]

    results, best = query_models(system, prompt, pick=strategy)
    engine = MultiModelQueryEngine()
    print(engine.format_comparison(results))
    if best:
        print(f"\n{'='*60}")
        print(f"🏆 最佳结果 [{strategy}]: {best.model_name}")
        print(f"{'='*60}")
        print(best.content)
