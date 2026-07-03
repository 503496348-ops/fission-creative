<!-- ZHIXIE_PROFILE_POLISH_START -->

<p align="left">
<a href="https://github.com/503496348-ops/fission-creative/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/503496348-ops/fission-creative?style=social"></a>
<a href="https://github.com/503496348-ops/fission-creative/issues"><img alt="GitHub issues" src="https://img.shields.io/github/issues/503496348-ops/fission-creative"></a>
<img alt="License" src="https://img.shields.io/github/license/503496348-ops/fission-creative">
<a href="https://github.com/503496348-ops/fission-creative/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/503496348-ops/fission-creative/actions/workflows/ci.yml/badge.svg"></a>
<img alt="Domain" src="https://img.shields.io/badge/domain-%E9%95%BF%E6%96%87%E5%88%9B%E4%BD%9C-blue">
</p>

## Highlights

- **Product**: Fission Creative / 裂变创作
- **Domain**: 长文创作
- **Maintained by**: [503496348-ops](https://github.com/503496348-ops) product matrix
- **Delivery posture**: one-click setup, doctor diagnostics, smoke test, convergence gate, and clean-clone verification are part of the maintenance standard.

## Quality Gates

```bash
./install.sh
python3 scripts/doctor.py
python3 scripts/smoke.py
python3 scripts/product_convergence_gate.py --json
python3 -m pytest tests/ -q
```

<!-- ZHIXIE_PROFILE_POLISH_END -->

## 一键安装 / One-click Quickstart

```bash
bash install.sh
python3 scripts/doctor.py
python3 scripts/smoke.py
```

- `bash install.sh`：自动执行 setup + smoke，适合第一次使用。
- `python3 scripts/doctor.py`：检查环境、入口文件和产品门禁，失败时给出修复建议。
- `python3 scripts/smoke.py`：执行产品收敛门禁和轻量核心冒烟验证。

# 裂变创作 · Fission Creative

> **v6.0.0** | GPL v3 | AtomCollide-智械工坊团队
>
> 基于 [lingfengQAQ/webnovel-writer](https://github.com/lingfengQAQ/webnovel-writer) 改造，适配 [Hermes Agent](https://hermes-agent.nousresearch.com) 平台。

---

## 🤔 解决什么问题？

用 AI 写长篇网文，最大的两个敌人是 **遗忘** 和 **幻觉**：

| 问题 | 表现 | 后果 |
|------|------|------|
| **遗忘** | 写到第50章忘了第3章埋的伏笔 | 伏笔断裂、前后矛盾 |
| **幻觉** | 凭空编造新角色、新设定 | 世界观崩塌、读者弃书 |
| **节奏失控** | 不知道哪里该爽、哪里该铺垫 | 追读率暴跌 |
| **风格漂移** | 前后文风不一致 | AI 味过重、代入感消失 |

裂变创作通过 **合同驱动的事实管理 + 结构化大纲 + 六维审查 + Anti-AI 润色** 四板斧，让 AI 写到第200章依然记得住设定、接得住伏笔、守得住大纲。

支持 **200万字量级** 的长篇连载创作，覆盖 **37种网文题材**。

---

## 🚀 快速开始（5步上手）

### 第1步：克隆项目

```bash
git clone https://github.com/503496348-ops/fission-creative.git \
  ~/.hermes/profiles/default/skills/fission-creative
```

### 第2步：初始化你的书

```bash
# 在 Hermes Agent 中输入：
/webnovel-init
```

系统会通过分阶段交互，引导你完成：
- 📖 题材选择（37种可选）
- 🌍 世界观搭建
- 👤 核心角色设计
- 📋 总纲与伏笔规划

生成完整的项目骨架（大纲/设定集/正文/审查报告等目录）。

### 第3步：规划卷纲 & 写第一章

```bash
/webnovel-plan 1      # 规划第1卷：拆章、定时间线、补设定
/webnovel-write 1     # 写第1章：上下文组装→起草→审查→润色→事实提取→备份
```

### 第4步：审查质量

```bash
/webnovel-review 1    # 对第1章进行六维审查
/webnovel-review 1-5  # 批量审查第1-5章
```

### 第5步：查看面板

```bash
/webnovel-dashboard   # 启动可视化面板，浏览项目状态、实体图谱、章节内容
```

> 📖 **小白使用说明书**: [飞书文档](https://vcnvmnln7wit.feishu.cn/docx/PlNpd0I6To00J7xCdVMcltfjnZe)

---

## 📋 7个子Skill命令速查表

| 命令 | 功能 | 典型用法 |
|------|------|----------|
| `/webnovel-init` | 🏗️ 深度初始化 | 创建新书项目，搭建骨架和设定集 |
| `/webnovel-plan` | 📐 卷纲规划 | 基于总纲拆卷、拆章、补时间线 |
| `/webnovel-write` | ✍️ 章节创作 | 完整流水线：上下文→起草→审查→润色→记录→备份 |
| `/webnovel-review` | 🔍 质量审查 | 六维审查：爽点/一致性/节奏/OOC/连贯性/追读力 |
| `/webnovel-query` | 🔎 状态查询 | 查询角色状态、伏笔、实体关系等 |
| `/webnovel-learn` | 📝 经验记录 | 把好用的写法存进项目长期记忆 |
| `/webnovel-dashboard` | 📊 可视化面板 | 只读浏览项目状态、实体图谱、章节内容 |

---

## 🔬 六维审查说明

每次写作后，系统自动对章节进行六维质量审查：

| 维度 | 检查内容 | 评分范围 |
|------|----------|----------|
| **爽点密度** | 是否每章有至少1个爽点/钩子 | 0-10 |
| **设定一致性** | 是否与已有设定矛盾 | 0-10 |
| **节奏控制** | 起承转合是否合理，是否有拖沓或跳跃 | 0-10 |
| **OOC检测** | 角色行为是否符合人设 | 0-10 |
| **连贯性** | 与前文衔接是否自然，伏笔是否接住 | 0-10 |
| **追读力** | 章末钩子是否足够强，读者会不会点下一章 | 0-10 |

审查报告存储在 `审查报告/` 目录，低分项会被标记并给出修改建议。

### 防幻觉三定律

1. **大纲即法律** — 遵循大纲，不擅自发挥
2. **设定即物理** — 遵守设定，不自相矛盾
3. **发明需识别** — 新实体必须入库管理

---

## 📁 文件结构

```
fission-creative/
├── SKILL.md                        # 主入口（Hermes技能定义）
├── README.md                       # 本文件
├── agents/                         # Agent 定义
│   ├── context-agent.md            #   写前上下文组装
│   ├── data-agent.md               #   事实提取 + CHAPTER_COMMIT
│   ├── reviewer.md                 #   六维审查逻辑
│   └── deconstruction-agent.md     #   参考书拆解
├── skills/                         # 7个子Skill
│   ├── webnovel-init/              #   初始化
│   ├── webnovel-plan/              #   卷纲规划
│   ├── webnovel-write/             #   章节创作
│   ├── webnovel-review/            #   质量审查
│   ├── webnovel-query/             #   状态查询
│   ├── webnovel-learn/             #   经验记录
│   └── webnovel-dashboard/         #   可视化面板
├── scripts/                        # Python 脚本
│   ├── webnovel.py                 #   CLI 入口
│   ├── plugin_architecture.py      #   插件架构（插件化架构）
│   ├── multi_model_query.py        #   多模型并行查询（新增）
│   ├── pdf_processor.py            #   PDF/LaTeX文档处理（新增）
│   └── data_modules/               #   核心数据模块
├── templates/                      # 模板
│   ├── genres/                     #   37个题材模板
│   └── output/                     #   输出模板（设定集/大纲等）
├── references/                     # 参考资料
├── dashboard/                      # 可视化面板前端
└── docs/                           # 文档
```

### 生成的项目结构

```bash
your-novel-project/
├── .story-system/          # 合同·提交·事件（事实源头）
├── .webnovel/              # 状态·索引·摘要·备份·长期记忆
├── 正文/                   # 章节正文
├── 大纲/                   # 总纲、卷纲、时间线、章纲
├── 设定集/                 # 世界观、角色、力量体系等
└── 审查报告/               # 六维审查报告
```

---

## 🎭 支持题材（37种）

<details>
<summary>点击展开完整题材列表</summary>

修仙 · 克苏鲁 · 历史古代 · 历史脑洞 · 古言 · 多子多福 · 女频悬疑 · 宫斗宅斗 · 年代 · 幻想言情 · 悬疑灵异 · 悬疑脑洞 · 抗战谍战 · 无限流 · 替身文 · 末世 · 民国言情 · 游戏体育 · 狗血言情 · 现实题材 · 现言脑洞 · 电竞 · 直播文 · 知乎短篇 · 种田 · 科幻 · 系统流 · 职场婚恋 · 西幻 · 规则怪谈 · 豪门总裁 · 都市异能 · 都市日常 · 都市脑洞 · 青春甜宠 · 高武 · 黑暗题材

</details>

---

## ❓ FAQ

**Q: 写一本书大概需要多少时间？**
A: 初始化（init）约15-30分钟，每章写作（write）约5-10分钟，具体取决于章节长度和复杂度。

**Q: 可以中途换题材/改大纲吗？**
A: 可以。用 `/webnovel-init` 重新初始化，或手动编辑大纲文件。系统会自动适配新的设定。

**Q: 支持英文/其他语言吗？**
A: 目前专注中文网文创作，题材模板和Anti-AI指南均为中文优化。理论上可以扩展其他语言。

**Q: 需要什么环境？**
A: 需要 [Hermes Agent](https://hermes-agent.nousresearch.com) 运行环境。依赖 Python 3.10+，安装 `pip install -r requirements.txt`。

**Q: Embedding/Rerank 是必须的吗？**
A: 不是。核心功能不依赖向量检索。如果配置了 `EMBED_*` 和 `RERANK_*` 环境变量，查询功能会更精准。

**Q: 和直接用 ChatGPT/Claude 写有什么区别？**
A: 直接用 LLM 写长篇，写到后面会"失忆"和"编造"。裂变创作通过合同驱动的事实管理 + 结构化大纲 + 自动审查，保证200万字级别的设定一致性。

---

## 📄 License

[GPL v3](LICENSE)

---



---

## 🚀 加入AtomCollide-AI智能体实验室

**元素碰撞-AtomCollide-AI 智能体实验室** 是一个专注于AI领域的开源组织，汇聚了众多优秀学习者。

### 核心价值

**找工作：更省力，也更精准**
- 一线大厂内推通道（字节、阿里、腾讯等）
- 全链路求职赋能包（面试题库、简历优化、晋升指导）
- 线下技术沙龙 & 人脉网络

**学AI测试：真正落地，拒绝空谈**
- 从0到1实战落地体系（Skills、MCP、RAG、AI IDE等）
- 独家自研资料与工具矩阵
- 前沿技术同步与提效方案

### 知识库

- [踩坑合集](https://vcnvmnln7wit.feishu.cn/wiki/CjV9wG8IHiIpWikCdFEcxfErnne)
- [商业化案例库](https://vcnvmnln7wit.feishu.cn/wiki/LdIxwlrKGibFEVkWMocc2K9KnBh)
- [科普专栏](https://vcnvmnln7wit.feishu.cn/wiki/K1RPwM8zji9ZchkxlOmcivUgnJe)
- [Open Build](https://vcnvmnln7wit.feishu.cn/wiki/CThswol0PiNJJbkhgT1cZIxanLb)
- [LLM/Agent/研究报告知识库](https://vcnvmnln7wit.feishu.cn/wiki/KwGQwS2TciT2EdkSBBtcYnbsnSd)
- [Skill封装合集](https://vcnvmnln7wit.feishu.cn/wiki/PDfpwqJZUibTyBkUa7TcZZ6Onpd)
- [社区治理运营知识库](https://vcnvmnln7wit.feishu.cn/wiki/MSEGwrdnTiiF9Dk8qCVcNW6InJg)

### 加入社群

| 社群 | 链接 |
|------|------|
| AI探索交流1区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=074vd565-6084-455c-ac52-9703e89a0697) |
| AI探索交流2区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=60bj94f0-1a67-48a7-abbb-9172b161c2b0) |
| AI探索交流3区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=13do1920-db46-4444-b635-005680beaf58) |
| AI探索交流4区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=f17o1b86-06f6-4f10-911a-69a299a25fe3) |
| AI探索交流5区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=2bbh6ab6-22c2-4753-b973-74bb1a2edcc9) |
| AI探索交流6区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=d19r19f7-2f47-42ba-b1ec-cb0342cf2e80) |
| AI探索交流7区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=fe9vdacc-7316-4b4d-ae4a-fdbcf56315e6) |
| AI探索交流8区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=103kfae8-1fd7-424f-984f-d66c210e42d1) |
| AI探索交流9区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=239p3cad-2f83-4baa-a230-f40386067548) |
| AI探索交流10区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=880r7cf5-3638-45ff-afb9-7944de991872) |
| AI探索交流-网文作家 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=6a3v579b-ab43-4e1a-87f9-be63bab88da7) |
| AI探索交流群-音乐达人 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=76at299e-73da-4eeb-9eba-32161e98f2f8) |
| AI探索交流群-微笑驿站 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=f2av73d0-6bb4-4a9f-9095-5fbbe83e49ec) |

---

*AtomCollide-智械工坊团队出品*

---

## 组织与社群入口

**元素碰撞 · AtomCollide-AI 智能体实验室**：面向学习者、创作者与自动化实践者，持续沉淀可复用的 AI Agent 产品、工作流与工程经验。使命：**for the learner**。

> 请选择 1 个常用社群加入，内容全域同步，无需重复加入。

### 知识库

| 知识库 | 链接 |
|---|---|
| 踩坑合集 | [进入](https://vcnvmnln7wit.feishu.cn/wiki/CjV9wG8IHiIpWikCdFEcxfErnne) |
| 商业化案例库 | [进入](https://vcnvmnln7wit.feishu.cn/wiki/LdIxwlrKGibFEVkWMocc2K9KnBh) |
| 科普专栏 | [进入](https://vcnvmnln7wit.feishu.cn/wiki/K1RPwM8zji9ZchkxlOmcivUgnJe) |
| Open Build | [进入](https://vcnvmnln7wit.feishu.cn/wiki/CThswol0PiNJJbkhgT1cZIxanLb) |
| LLM / Agent / 研究报告 | [进入](https://vcnvmnln7wit.feishu.cn/wiki/KwGQwS2TciT2EdkSBBtcYnbsnSd) |
| Skill 封装合集 | [进入](https://vcnvmnln7wit.feishu.cn/wiki/PDfpwqJZUibTyBkUa7TcZZ6Onpd) |
| 社区治理运营 | [进入](https://vcnvmnln7wit.feishu.cn/wiki/MSEGwrdnTiiF9Dk8qCVcNW6InJg) |

### 社群邀请

| 社群 | 链接 |
|---|---|
| AI 探索交流 1 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=074vd565-6084-455c-ac52-9703e89a0697) |
| AI 探索交流 2 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=60bj94f0-1a67-48a7-abbb-9172b161c2b0) |
| AI 探索交流 3 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=13do1920-db46-4444-b635-005680beaf58) |
| AI 探索交流 4 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=f17o1b86-06f6-4f10-911a-69a299a25fe3) |
| AI 探索交流 5 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=2bbh6ab6-22c2-4753-b973-74bb1a2edcc9) |
| AI 探索交流 6 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=d19r19f7-2f47-42ba-b1ec-cb0342cf2e80) |
| AI 探索交流 7 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=fe9vdacc-7316-4b4d-ae4a-fdbcf56315e6) |
| AI 探索交流 8 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=103kfae8-1fd7-424f-984f-d66c210e42d1) |
| AI 探索交流 9 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=239p3cad-2f83-4baa-a230-f40386067548) |
| AI 探索交流 10 区 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=880r7cf5-3638-45ff-afb9-7944de991872) |
| AI 探索交流 — 网文作家 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=6a3v579b-ab43-4e1a-87f9-be63bab88da7) |
| AI 探索交流群 — 音乐达人 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=76at299e-73da-4eeb-9eba-32161e98f2f8) |
| AI 探索交流群 — 微笑驿站 | [加入](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=f2av73d0-6bb4-4a9f-9095-5fbbe83e49ec) |

---

AtomCollide-智械工坊团队出品。更多产品见：[AtomCollide Product Matrix](https://503496348-ops.github.io/atomcollide-product-matrix/)。


## 示例输出

本仓库的最小可验证使用路径：

1. 阅读 README 的 Quick Start / 使用说明，完成本地安装或配置。
2. 按仓库提供的命令、脚本或入口运行一次最小任务。
3. 对照本产品定位验证输出：**裂变创作（Fission Creative）** 属于 **长文创作** 产品，目标是把输入材料转化为可检查、可复用的结果。
4. 若运行环境暂不可用，先通过 README、CHANGELOG、CI 状态和源码结构完成静态验收，再补充真实截图或录屏。

> 维护要求：后续每次发布都应把真实运行截图、CLI 输出、网页截图或 API 响应样例补充到本节，避免仓库首页只描述能力、不展示结果。

## 2026-07-03 产品收敛门禁

- 新增 `scripts/product_convergence_gate.py`：从远端干净 clone 后可运行 `python3 scripts/product_convergence_gate.py --json`，检查 SKILL/README、入口文件、smoke 目标、测试与外部融合引用是否自洽。
- 新增 `tests/test_product_convergence_gate.py`：确保门禁在产品仓库中真实可执行，避免后续增强只停留在孤岛模块。
