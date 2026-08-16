# 安全说明（SECURITY.md）

> 本文件说明本项目（kic-ai-cn）的安全机制、已知风险与漏洞上报方式。

## 一、项目自带的三层安全防线

| 层 | 机制 | 触发 |
|---|---|---|
| L1 规则扫描 | `security-patterns.yaml`（14 条规则：密钥/AWS/私钥/SQL注入/eval 等）+ `scripts/check-secrets.py` | 本机 pre-commit 钩子 + GitHub Actions（push/PR 自动），命中即标红 |
| L2 LLM 轻量审查 | `scripts/security-review.py --diff / --staged` | 手动，DeepSeek 审未提交改动 |
| L3 LLM 深度审查 | `scripts/security-review.py --commits A..B / --all` | 手动，审提交历史 / 全仓库 |

详见 README「三层安全防线」章节。

## 二、密钥与 API Key 处理（务必遵守）

- **本项目仓库内不存储任何 API Key / 密码 / 凭据**，提交前由 L1 钩子自动拦截。
- API Key 只通过以下渠道提供（按优先级）：
  1. 命令行参数 `--api-key`
  2. 环境变量 `DEEPSEEK_API_KEY` / `OPENAI_API_KEY`
  3. 插件配置 `~/.kic-ai/config.json`（与 KiC-AI 插件共用）
  4. CI 场景：GitHub Actions Secrets（fork 的 PR 默认拿不到 Secrets）
- 若误提交了密钥：立即在对应平台**作废重建**，并用 `git filter-repo` 清理历史。

## 三、多厂商 API 支持与已知风险

`security-review.py` 支持 OpenAI 兼容多厂商（deepseek/openai/zhipu/qwen/minimax/custom）。

**使用侧风险（不属于仓库本身）：**

1. **代码外泄**：审查脚本会把所选范围内的代码发送到配置的 API 地址。
   - 仓库代码本身公开，无风险；
   - 私有项目请确认厂商可信；不知名地址请勿使用。
2. **密钥外泄**：Key 以 `Authorization: Bearer` 头发送给配置的地址。
   - 不要把 Key 配给不可信端点。
3. **合规**：公司私有代码送第三方厂商需符合公司政策。

**仓库侧缓解：**

- 零第三方运行时依赖（仅 Python 标准库），无供应链风险；
- 系统提示已加防提示词注入说明（被审查代码按"数据"处理）；
- 审查输出仅为建议，不自动执行任何操作。

## 四、漏洞上报（Responsible Disclosure）

- 公开漏洞：请走 GitHub 私有漏洞上报（Security → Report a vulnerability），或发 Issue 时**不要附带真实密钥**。
- 敏感问题（含密钥泄露类）：请先通过仓库 GitHub Issues 联系维护者，处理后再公开。
- 本项目所有安全工具的输出（扫描/审查报告）仅作辅助，关键决策请人工复核。

## 五、维护承诺

- 规则库（`security-patterns.yaml`）可持续扩充，改完即生效；
- 扫描/审查脚本零依赖、跨平台（Windows/macOS/Linux）；
- 若发现本仓库代码本身的安全问题，欢迎上报，我们会及时处理。
