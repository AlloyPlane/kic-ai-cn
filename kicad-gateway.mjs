// kicad-gateway.mjs — 把 MCP 工具调用桥接给 Harness 会话
// 用法: node kicad-gateway.mjs <serverDir> <requestFile> <resultFile>
import { spawn } from 'node:child_process';
import { createInterface } from 'node:readline';
import fs from 'node:fs';

const serverDir = process.argv[2];
const reqFile = process.argv[3];
const resFile = process.argv[4];

let req;
try {
  req = JSON.parse(fs.readFileSync(reqFile, 'utf8'));
} catch (e) {
  fs.writeFileSync(resFile, JSON.stringify({ ok: false, error: 'bad request file: ' + e.message }));
  process.exit(0);
}

const child = spawn('node', ['dist/index.js'], {
  cwd: serverDir,
  env: {
    ...process.env,
    KICAD_PYTHON: 'D:\\kicad\\bin\\python.exe',
    PYTHONPATH: serverDir + '\\python',
    KICAD_MCP_PY_LOG_LEVEL: 'warning',
    LOG_LEVEL: 'warning',
  },
  stdio: ['pipe', 'pipe', 'pipe'],
});

const responses = {};
let stderrTail = '';
createInterface({ input: child.stdout }).on('line', (line) => {
  try {
    const m = JSON.parse(line);
    if (m.id !== undefined) responses[m.id] = m;
  } catch {}
});
child.stderr.on('data', (d) => {
  stderrTail = (stderrTail + d.toString()).slice(-2500);
});

function call(id, method, params = {}) {
  child.stdin.write(JSON.stringify({ jsonrpc: '2.0', id, method, params }) + '\n');
  return new Promise((resolve, reject) => {
    const t0 = Date.now();
    const iv = setInterval(() => {
      if (responses[id]) { clearInterval(iv); resolve(responses[id]); }
      else if (Date.now() - t0 > 150000) { clearInterval(iv); reject(new Error('timeout: ' + method)); }
    }, 100);
  });
}

function done(obj) {
  fs.writeFileSync(resFile, JSON.stringify(obj));
  console.log(JSON.stringify(obj).slice(0, 6000));
  try { child.kill(); } catch {}
  setTimeout(() => process.exit(0), 300);
}

try {
  const init = await call('init', 'initialize', {
    protocolVersion: '2025-06-18',
    capabilities: {},
    clientInfo: { name: 'kicad-gateway', version: '1.0' },
  });
  child.stdin.write(JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized' }) + '\n');
  const res = await call('tool', 'tools/call', { name: req.tool, arguments: req.args ?? {} });
  const payload = res.result ?? res.error ?? {};
  if (payload.isError === true) {
    done({ ok: false, tool: req.tool, error: payload });
  } else {
    const content = payload.content ?? [];
    const text = Array.isArray(content)
      ? content.map((c) => (typeof c === 'object' ? (c.text ?? JSON.stringify(c)) : String(c))).join('\n')
      : JSON.stringify(payload);
    done({ ok: true, tool: req.tool, text: String(text).slice(0, 6000) });
  }
} catch (e) {
  done({ ok: false, error: String((e && e.message) || e), stderr: stderrTail.slice(-800) });
}
