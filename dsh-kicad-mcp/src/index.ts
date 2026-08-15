/**
 * dsh-kicad-mcp — DeepSeek Harness 的 KiCad MCP 桥接插件。
 *
 * 原理：基于 @deepseek-ai/dsh-mcp-client，把 KiCad MCP 服务器
 * （KiCAD-MCP-Server / Konnect）注册进 ctx.tools，
 * 工具以 mcp__<serverName>__<rawName> 形式暴露给 agent。
 * 多服务器 = 多个 mcp-client 实例。
 *
 * 参考：packages/mcp/mcp-client（@deepseek-ai/dsh-mcp-client）
 */
import type { Context } from '@deepseek-ai/cordis'
import z from '@deepseek-ai/schemastery'
import * as McpClient from '@deepseek-ai/dsh-mcp-client'

/** Cordis 插件名（诊断/配置用）。 */
export const name = 'kicad-mcp'

/** 依赖的服务。 */
export const inject = ['tools'] as const

/** 一个 KiCad MCP 服务器（stdio 传输）的配置。 */
export interface KiCadServer {
  /** 稳定命名空间，工具名为 mcp__<serverName>__<rawName>，须匹配 [A-Za-z0-9_-]{1,32}。 */
  serverName: string
  /** 启动命令，如 node / konnect.exe。 */
  command: string
  /** 命令参数，不经过 shell。 */
  args: string[]
  /** 附加环境变量（KICAD_PYTHON / PYTHONPATH 等）。 */
  env: Record<string, string>
  /** 子进程工作目录（MCP 服务器所在目录）。 */
  cwd: string
  /** 单次工具调用超时（毫秒）。 */
  toolCallTimeoutMs?: number
}

/** 插件配置。 */
export interface Config {
  /** 要连接的 KiCad MCP 服务器列表。 */
  servers: KiCadServer[]
  /** 初始连接或工具同步失败时是否让插件激活失败。 */
  failOnStartupError?: boolean
}

const KiCadServer: z<KiCadServer> = z.object({
  serverName: z.string().pattern(/^[A-Za-z0-9_-]{1,32}$/),
  command: z.string(),
  args: z.array(String).default([]),
  env: z.dict(String).default({}),
  cwd: z.string().default(''),
  toolCallTimeoutMs: z.number().default(120000),
})

export const Config: z<Config> = z.object({
  servers: z.array(KiCadServer).default([]),
  failOnStartupError: z.boolean().default(false),
})

/**
 * 便捷构造：根据 KiCad 安装目录与 MCP 服务器目录生成标准 stdio 配置。
 * 适用于 mixelpixx/KiCAD-MCP-Server（node dist/index.js）。
 */
export function stdioServer(options: {
  serverName: string
  mcpServerDir: string
  kicadPython: string
  pythonPath?: string
}): KiCadServer {
  return {
    serverName: options.serverName,
    command: 'node',
    args: ['dist/index.js'],
    env: {
      KICAD_PYTHON: options.kicadPython,
      ...(options.pythonPath !== undefined ? { PYTHONPATH: options.pythonPath } : {}),
    },
    cwd: options.mcpServerDir,
    toolCallTimeoutMs: 120000,
  }
}

/**
 * 便捷构造：连接 Konnect（单个原生二进制，KiCad 10 的 IPC 方案）。
 */
export function konnectServer(options: {
  serverName: string
  konnectBinary: string
  kicadPython: string
}): KiCadServer {
  return {
    serverName: options.serverName,
    command: options.konnectBinary,
    args: [],
    env: { KICAD_PYTHON: options.kicadPython },
    cwd: '',
    toolCallTimeoutMs: 120000,
  }
}

/** 插件入口：为每个配置的服务器挂载一个 mcp-client 实例。 */
export function apply(ctx: Context, config: Config): void {
  for (const server of config.servers) {
    ctx.plugin(McpClient, {
      transport: 'stdio' as const,
      serverName: server.serverName,
      command: server.command,
      args: server.args,
      env: server.env,
      cwd: server.cwd,
      toolCallTimeoutMs: server.toolCallTimeoutMs ?? 120000,
      failOnStartupError: config.failOnStartupError ?? false,
    })
  }
}
