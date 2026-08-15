# KIC-AI 中文增强版（KIC-AI CN）

基于 [jochemkroon/KiC-AI](https://github.com/jochemkroon/KiC-AI)（MIT）的深度增强分支：
**云端 API + 中文界面 + 联网搜索 + Harness 网关接管 KiCad**。

> 原版 KiC-AI 只支持本地 Ollama 且界面为英文。本分支在保留原版全部功能的基础上，让它真正可用、好用。

---

## ✨ 特性

| 特性 | 说明 |
|---|---|
| 🌐 **云端大模型 API** | 内置 DeepSeek / OpenAI / 智谱GLM / 通义千问 / MiniMax / 自定义（OpenAI 兼容），填 API Key 即用；不填 Key 自动回退本地 Ollama |
| 🇨🇳 **中文界面** | 中文为主 + 中英一键切换，英文原文保留对照（翻译不准可看原件） |
| 🔎 **联网搜索** | 融合 DeepSeek 原生搜索（`web_search_20250305`，Anthropic 兼容接口）：消息含"搜索/最新/今天"等词自动联网，或点 **🌐 联网搜索** 按钮；结果注入回答上下文并展示来源 |
| 🤖 **Harness 网关接管 KiCad** | 配套 `kicad-gateway.mjs`：让 DeepSeek Harness 会话通过 MCP 直接操作 KiCad（建工程/放器件/DRC/导 Gerber） |
| 🛠 稳定性修复 | 配置窗口滚动（兼容 wxPython 4.2，修复 `SetupScrolling` 不存在问题） |

---

## 📦 安装

### 1. 安装插件（二选一）

**A. 替换已安装副本（推荐）**
把本仓库 `plugins/` 下两个文件复制到 KiCad 插件目录：

```
%APPDATA%\kicad\10.0\scripting\plugins\kic_ai\
```

**B. 手动安装插件**
1. KiCad 需要 9.0+（含 Python 插件支持）
2. 安装依赖：`pip install requests`（用 KiCad 自带的 Python）
3. 按上面路径放置文件，重启 KiCad

### 2. 配置（首次使用）

1. 打开 KiCad → **PCB 编辑器** → 工具栏 **🤖 图标**
2. ⚙️ **设置** → **API 设置** 页签：
   - **AI 模型（LLM）**：Provider 选 `deepseek`（或你有的平台），粘贴 **API Key**，Model 留空默认 `deepseek-chat`
   - **联网搜索**：默认开启；搜索模型默认 `deepseek-v4-flash`（若报模型不存在，改为 `deepseek-chat`）
3. **保存** → 开始聊天

> 🔑 需要有效且有余量的 DeepSeek API Key（https://platform.deepseek.com）
> 联网搜索与 AI 对话共用同一个 Key，每次联网 = 一次额外 API 调用。

---

## 🌐 联网搜索原理（同 DeepSeek Harness 官方实现）

调用 DeepSeek 的 **Anthropic 兼容 Messages API**：

```
POST https://api.deepseek.com/anthropic/v1/messages
模型: deepseek-v4-flash   工具: { type: "web_search_20250305", name: "web_search" }
```

服务端执行原生搜索 → 返回结构化结果（标题/URL/摘要/时间）→ 注入给大模型回答。

---

## 🤖 Harness 网关：让 AI 直接操作 KiCad

`kicad-gateway.mjs` 把 MCP 工具调用桥接给 DeepSeek Harness 会话：

```
Harness 会话 → request.json → kicad-gateway.mjs → KiCAD-MCP-Server(153工具) → KiCad
```

前置：`D:\kicad\KiCAD-MCP-Server`（npm install + build 后），KiCad 10 含 Python。

用法（每次一个工具调用）：
```bash
node kicad-gateway.mjs <serverDir> <request.json> <result.json>
```

`request.json`：`{"tool": "create_project", "args": {"name": "demo"}}`
`result.json`：网关写回执行结果。

> 💡 **生态展望**：DeepSeek Harness 自带 `@deepseek-ai/dsh-mcp-client`，可原生把 MCP 服务器注册为 agent 工具。更优雅的集成方式是给 Harness 写一个 KiCad MCP 插件（见下文"参与 Harness 生态"）。

---

## 🧭 参与 DeepSeek Harness 生态

Harness 是插件化的（Cordis 架构），生态参与点：

1. **原生 MCP 插件**：基于 `packages/mcp/mcp-client` 写一个 `dsh-kicad-mcp` 插件，把 Konnect / KiCAD-MCP-Server 注册到 `ctx.tools`，让任何 Harness 会话直接获得 PCB 工具
2. **工具插件**：仿照 `packages/web/tool-web`（`defineTool`）写 `dsh-pcb-tools`，封装 `kicad-cli` 的 DRC/Gerber 导出为 agent 工具
3. **搜索/LLM 提供商**：仿照 `packages/web/web-search-deepseek` 提供新 provider

仓库：https://github.com/deepseek-ai/deepseek-harness

---

## 🔐 安全防线（三层，Qoder/CodeSec 风格）

- **L1 规则扫描**：`security-patterns.yaml` 规则库（密钥/AWS/私钥/SQL注入/eval 等 14 条，可自定义）+ `scripts/check-secrets.py`
  - 本机：pre-commit 钩子自动拦（提交前扫暂存区）
  - 云端：GitHub Actions（`.github/workflows/security-scan.yml`）push/PR 自动跑，命中标红
- **L2/L3 LLM 审查**：`scripts/security-review.py` 用 DeepSeek 对 diff / commit 范围 / 全仓库做一轮"安全工程师"式审查（输出严重级别+修复建议）
  ```bash
  python scripts/security-review.py --diff          # L2: 未提交改动
  python scripts/security-review.py --commits A..B  # L3: 提交范围
  python scripts/security-review.py --all           # L3: 全仓库采样
  ```
  API Key 自动读取：`DEEPSEEK_API_KEY` 环境变量 或 `~/.kic-ai/config.json`
- 想加规则？往 `security-patterns.yaml` 加一条即生效（改完不用装任何东西）


## 📜 许可与致谢

- **MIT License**（保留原作者 Jochem © 2025 版权声明；本增强分支版权归贡献者所有）
- 原项目：[jochemkroon/KiC-AI](https://github.com/jochemkroon/KiC-AI)
- 依赖的 Harness 实现：DeepSeek Harness（`@deepseek-ai/dsh-mcp-client`、`web-search-deepseek`）
- MCP 服务器：[mixelpixx/KiCAD-MCP-Server](https://github.com/mixelpixx/KiCAD-MCP-Server)（MIT）、[mixelpixx/Konnect](https://github.com/mixelpixx/Konnect)（AGPL，未包含在本仓库内）

> ⚠️ 本仓库只包含我们的增强代码与网关，**不包含** KiCAD-MCP-Server / Konnect 本体，请按各自许可证单独获取。