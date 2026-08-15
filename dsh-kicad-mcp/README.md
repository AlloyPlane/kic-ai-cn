# dsh-kicad-mcp

DeepSeek Harness 的 KiCad 桥接插件：把 **KiCAD-MCP-Server / Konnect** 注册进 agent 工具表（`ctx.tools`），让任何 Harness 会话直接获得 PCB 设计能力（建工程、原理图、布线、DRC、Gerber 导出……）。

底层基于官方 [@deepseek-ai/dsh-mcp-client](https://github.com/deepseek-ai/deepseek-harness/tree/main/packages/mcp/mcp-client)。

## 安装

```bash
npm install dsh-kicad-mcp
# 或从源码构建：
npm install && npm run build
```

## 配置（cordis.yml 片段）

```yaml
plugins:
  - from: dsh-kicad-mcp
    config:
      failOnStartupError: false
      servers:
        - serverName: kicad        # 工具名前缀 mcp__kicad__*
          command: node
          args: ['dist/index.js']
          cwd: 'D:/kicad/KiCAD-MCP-Server'
          env:
            KICAD_PYTHON: 'D:/kicad/bin/python.exe'
            PYTHONPATH: 'D:/kicad/KiCAD-MCP-Server/python'
          toolCallTimeoutMs: 120000
        - serverName: konnect      # 第二个服务器 = 第二个实例
          command: 'D:/kicad/Konnect/bin/konnect.exe'
          args: []
          cwd: ''
          env:
            KICAD_PYTHON: 'D:/kicad/bin/python.exe'
          toolCallTimeoutMs: 120000
```

或直接用代码里提供的便捷函数生成配置（`stdioServer` / `konnectServer`）。

## 使用

配置加载后，agent 会话里会出现 `mcp__kicad__create_project`、`mcp__kicad__run_drc`、`mcp__konnect__*` 等工具，直接对话即可让 AI 操作 KiCad。

## 许可

MIT。KiCAD-MCP-Server 为 MIT，Konnect 为 AGPL-3.0（各自获取，勿并入本仓库）。
