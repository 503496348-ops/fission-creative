---
name: fission-creative
description: 长篇网文创作系统 — 解决AI写作中的「遗忘」和「幻觉」问题，支持200万字量级连载创作。Story System合同驱动+CBN/CPNs/CEN结构化大纲+六维审查+Anti-AI指南。
version: 6.0.0
author: AtomCollide-智械工坊团队
last_refactored: 2026-06-04
tags: [writing, novel, long-form, story-system, anti-ai, rag]
requires_tools: [read_file, write_file, patch, search_files, terminal, clarify, skill_view]
requires_toolsets: [file, terminal]
required_environment_variables:
  - WORKSPACE_ROOT
---

## When to use

激活此技能的场景：
- 用户要求创建/续写长篇网文项目（百万字级别连载）
- 用户询问故事设定、角色关系、伏笔追踪等项目内信息
- 用户需要章节质量审查（六维审查）
- 用户需要卷纲规划或章节大纲生成
- 用户要求启动可视化面板查看项目状态

**不激活**的场景：
- 用户只是写一篇短文/博客（不需要此技能）
- 用户询问通用写作技巧（用 general knowledge）
- 用户要求写诗歌/剧本（非网文体裁）

## 定位

fission-creative是一套面向**长篇连载**的一致性系统，不是写完就忘的一次性生成器。

核心解决的问题：让AI写到几百章，依然记得住设定、接得住伏笔、守得住大纲。

## 核心能力（7个子Skill）

| 子Skill | 功能 | 触发方式 |
|---------|------|---------|
| `webnovel-init` | 深度初始化：分阶段问答，搭建书骨架、设定集、总纲和初始状态 | `/webnovel-init` |
| `webnovel-plan` | 卷纲规划：基于总纲拆卷、拆章、补时间线，写回新增设定 | `/webnovel-plan {volume}` |
| `webnovel-write` | 章节创作：上下文→起草→审查→润色→记录事实→备份 | `/webnovel-write {chapter}` |
| `webnovel-review` | 质量审查：爽点/一致性/节奏/OOC/连贯性/追读力六维审查 | `/webnovel-review {chapter}` |
| `webnovel-query` | 状态查询：角色/伏笔/节奏/实体关系/运行时信息 | `/webnovel-query {query}` |
| `webnovel-learn` | 项目学习：把好用的写法记下来，存进项目长期记忆 | `/webnovel-learn {pattern}` |
| `webnovel-dashboard` | 可视化面板：只读浏览项目状态、实体图谱、章节内容 | `/webnovel-dashboard` |

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Hermes Agent                           │
├─────────────────────────────────────────────────────────────┤
│  Skills (7个):                                             │
│    init / plan / write / review / query / learn / dashboard │
├─────────────────────────────────────────────────────────────┤
│  Agents (3个):                                             │
│    Context Agent / Data Agent / Reviewer (含六维审查)        │
├─────────────────────────────────────────────────────────────┤
│  Data Layer:                                               │
│    state.json / index.db (SQLite) / vectors.db             │
├─────────────────────────────────────────────────────────────┤
│  Story System:                                             │
│    .story-system/ (合同·提交·事件)                           │
└─────────────────────────────────────────────────────────────┘
```

## 核心设计理念

### 防幻觉三定律

| 定律 | 说明 |
|------|------|
| **大纲即法律** | 遵循大纲，不擅自发挥 |
| **设定即物理** | 遵守设定，不自相矛盾 |
| **发明需识别** | 新实体必须入库管理 |

### Story System 合同驱动

- `.story-system/`：唯一的事实源头（写前真源）
- `CHAPTER_COMMIT`：写后事实源
- `.webnovel/state.json`、`index.db`、`summaries/`：投影/只读视图

### CBN/CPNs/CEN 结构化大纲

每章固定结构：
- **CBN**（章节起点）：1个
- **CPNs**（推进节点）：2-4个
- **CEN**（章节终点）：1个
- 相邻章节 CEN → 下一章 CBN 必须逻辑承接

## 使用流程

### 1. 初始化一本书

```bash
/webnovel-init
```

通过分阶段交互收集创作信息，生成项目骨架：
```
project-root/
├── .story-system/        # 合同、章节提交和事件审计
├── .webnovel/            # 状态、索引、摘要、备份和长期记忆
├── 正文/                  # 章节正文
├── 大纲/                  # 总纲、卷纲、时间线和章纲
├── 设定集/                # 世界观、角色、力量体系等设定
└── 审查报告/              # 章节审查报告
```

### 2. 规划卷纲

```bash
/webnovel-plan 1      # 规划第 1 卷
```

基于总纲细化卷纲、时间线与章纲，增量写回设定集。

### 3. 写章节

```bash
/webnovel-write 1     # 写第 1 章
```

完整流水线：
1. context-agent 生成写作任务书
2. 起草正文
3. reviewer 审查（六维）
4. 润色（Anti-AI + 风格适配）
5. data-agent 提取事实 + CHAPTER_COMMIT
6. Git 备份

### 4. 审查章节

```bash
/webnovel-review 1-5  # 审查第 1-5 章
```

### 5. 查询状态

```bash
/webnovel-query 伏笔          # 查询伏笔
/webnovel-query 萧炎 角色状态  # 查询角色状态
```

### 6. 可视化面板

```bash
/webnovel-dashboard
```

## 目录结构

```
fission-creative/
├── SKILL.md                    # 本文件（主入口）
├── agents/                     # Agent定义
│   ├── context-agent.md        # 写前上下文组装
│   ├── data-agent.md           # 事实提取+commit
│   ├── reviewer.md             # 六维审查
│   └── deconstruction-agent.md # 参考书拆解
├── skills/                     # 7个子Skill
│   ├── webnovel-init/
│   ├── webnovel-plan/
│   ├── webnovel-write/
│   ├── webnovel-review/
│   ├── webnovel-query/
│   ├── webnovel-learn/
│   └── webnovel-dashboard/
├── scripts/                    # Python脚本
│   ├── webnovel.py             # CLI入口
│   ├── data_modules/           # 核心数据模块
│   └── ...
├── templates/                  # 模板
│   ├── genres/                 # 37个题材模板
│   └── output/                 # 输出模板
├── references/                 # 参考资料
│   ├── genre-profiles.md       # 题材配置
│   ├── reading-power-taxonomy.md
│   └── shared/                 # 共享参考
└── dashboard/                  # 可视化面板
```

## 依赖

```bash
pip install -r requirements.txt
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `WORKSPACE_ROOT` | 工作区根目录 |
| `HERMES_HOME` | Hermes配置目录（默认`~/.hermes`） |
| `WEBNOVEL_HERMES_HOME` | 自定义Hermes目录 |
| `WEBNOVEL_PROJECT_ROOT` | 显式指定项目根目录 |
| `EMBED_BASE_URL/MODEL/API_KEY` | Embedding配置 |
| `RERANK_BASE_URL/MODEL/API_KEY` | Rerank配置 |

## 题材支持（37种）

修仙、克苏鲁、历史古代、历史脑洞、古言、多子多福、女频悬疑、宫斗宅斗、年代、幻想言情、悬疑灵异、悬疑脑洞、抗战谍战、无限流、替身文、末世、民国言情、游戏体育、狗血言情、现实题材、现言脑洞、电竞、直播文、知乎短篇、种田、科幻、系统流、职场婚恋、西幻、规则怪谈、豪门总裁、都市异能、都市日常、都市脑洞、青春甜宠、高武、黑暗题材

## License

GPL-3.0
