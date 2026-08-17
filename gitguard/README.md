# gitguard — Git 安全上传防护

一行命令，让本机**所有 git 仓库**在提交/推送时自动做安全扫描（灵感来自 Qoder 的思路），
并支持 LLM 深度审查（L2/L3）。

## 安装 / Install
```bash
python gitguard.py install     # 安装全局钩子（core.hooksPath → ~/.gitguard）
```

## 使用 / Usage

运行 `review` 时会出现模式菜单：
```
gitguard 安全审查模式:
  [1] 用当前使用的模型 (deepseek-v4-pro)   ← 自动读你正在用的模型，回车即用
  [2] 自定义模型（填 API 地址 / Key / 模型名） ← 现场填三要素
```

```bash
python gitguard.py scan              # 扫描当前仓库（提交钩子自动调用）
python gitguard.py scan --staged     # 只扫暂存区
python gitguard.py review --diff     # L2: 审未提交改动（LLM）
python gitguard.py review --commits A..B   # L3: 审提交范围
python gitguard.py review --all      # L3: 全仓库采样
python gitguard.py config            # 保存自定义模型三要素（以后免填）
python gitguard.py status            # 查看状态
python gitguard.py uninstall         # 卸载
```

## 特性 / Features
- **L1 规则扫描（自动）**：`security-patterns.yaml`（14 条：密钥/AWS/私钥/SQL注入/eval 等）
  在每次 `git commit`（暂存区）和 `git push`（全库）前自动运行，命中即拦截
- **L2/L3 LLM 审查（手动）**：DeepSeek 等多厂商 OpenAI 兼容 API，输出严重级别+修复建议
- **零依赖**：纯 Python 标准库；跨平台（Windows/macOS/Linux）
- **全局生效**：`core.hooksPath` 使本机所有仓库自动带防护

## API Key（L2/L3 需要）
读取顺序：命令行参数 > 环境变量 `DEEPSEEK_API_KEY` / `OPENAI_API_KEY` > `~/.gitguard/config.json` > `~/.kic-ai/config.json`（正在用的模型）。

## 原理 / How it works
`install` 把 pre-commit / pre-push 钩子装到 `~/.gitguard`，并设置全局 `core.hooksPath`。
钩子调用 `gitguard.py scan`，命中规则（密钥/危险模式）即阻止提交/推送。

## 许可 / License
MIT
