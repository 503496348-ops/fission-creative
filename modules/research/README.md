# 裂变创作 × GPT-Researcher 融合增强

## 融合来源
- **竞品**: assafelovic/gpt-researcher (27K⭐)
- **核心能力**: Plan-and-Solve 研究流水线 + 并行搜索 + 深度递归探索 + 引用报告

## 新增模块

### research_planner.py
研究规划器——将主题分解为结构化研究问题：
- `ResearchQuestion`: 带类型/优先级/子问题的研究问题
- `ResearchPlan`: 研究计划（问题列表 + 搜索查询 + 文档大纲）
- 5种问题类型：factual/analytical/comparative/evaluative/exploratory
- 支持 LLM 生成或启发式模板

### parallel_researcher.py
并行搜索引擎——多源同时搜索 + 结果聚合：
- `ParallelResearcher`: 并行搜索 + 去重 + 相关性评分
- `WebSearchProvider`: 网页搜索
- `DocumentSearchProvider`: 本地文档搜索
- 内容提取 + 领域权威度评分

### deep_explorer.py
深度探索器——递归树状主题探索：
- `ExplorationNode`: 知识树节点
- `DeepExplorer`: BFS+DFS混合遍历
- 重要性剪枝 + 环检测 + 安全限制
- 树扁平化 + 发现聚合

### report_publisher.py
报告发布器——结构化报告生成 + 引用管理：
- `Report`: 多节报告 + 引用追踪
- `ReportSection`: 带层级和引用的内容节
- `Citation`: 编号引用
- 输出格式：Markdown / HTML / JSON

## 流水线用法

```python
from research_planner import ResearchPlanner
from parallel_researcher import ParallelResearcher
from deep_explorer import DeepExplorer
from report_publisher import ReportPublisher

# 1. 规划
planner = ResearchPlanner()
plan = planner.plan("AI Agent Architecture", num_questions=5)

# 2. 并行搜索
researcher = ParallelResearcher()
results = researcher.research(plan.search_queries)

# 3. 深度探索
explorer = DeepExplorer(max_depth=2)
tree = explorer.explore("AI Agent Architecture")
all_findings = explorer.collect_all_findings(tree)

# 4. 发布报告
publisher = ReportPublisher()
report = publisher.publish(
    topic=plan.topic,
    outline=plan.outline,
    findings=all_findings.get("all_sources", []),
    sources=all_findings.get("all_sources", []),
)
publisher.save(report, "/tmp/report", fmt="markdown")
```
