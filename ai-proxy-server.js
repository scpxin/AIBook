/**
 * AI 代理服务器 - 通用 Node.js 版
 * 
 * 部署到任意支持 Node.js 的平台（Sealos DevBox / VPS / Railway / Render 等）
 * Node.js 18+ 内置 fetch，无需安装任何依赖
 * 
 * 启动: node ai-proxy-server.js
 * 默认端口: 8787
 * 
 * 路由:
 *   POST /api/ai/generate  - AI 请求代理
 *   GET  /health            - 健康检查
 */

const http = require('http');
const PORT = process.env.PORT || 8787;

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': '*',
};

function json(res, data, status) {
  res.writeHead(status || 200, { ...CORS_HEADERS, 'Content-Type': 'application/json' });
  res.end(JSON.stringify(data));
}

async function handleAIRequest(body) {
  const { endpoint, apiKey, model, messages, options } = body;

  if (!endpoint || !apiKey || !model || !messages) {
    return { error: '缺少必填字段: endpoint, apiKey, model, messages' };
  }

  const reqBody = {
    model: model,
    messages: messages,
    temperature: (options && options.temperature) || 0.7,
    max_tokens: (options && options.max_tokens) || 4096,
  };

  const resp = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + apiKey,
    },
    body: JSON.stringify(reqBody),
  });

  const data = await resp.json();

  if (!resp.ok) {
    const errMsg = data.error && data.error.message ? data.error.message : ('HTTP ' + resp.status);
    return { error: errMsg };
  }

  const content = (data.choices && data.choices[0] && data.choices[0].message)
    ? data.choices[0].message.content
    : '';

  return { content: content, usage: data.usage || null };
}

const server = http.createServer(async (req, res) => {
  // CORS preflight
  if (req.method === 'OPTIONS') {
    res.writeHead(204, CORS_HEADERS);
    res.end();
    return;
  }

  // Health check
  if (req.method === 'GET' && req.url === '/health') {
    json(res, { status: 'ok' });
    return;
  }

  // AI proxy
  if (req.method === 'POST' && req.url === '/api/ai/generate') {
    try {
      let raw = '';
      req.on('data', chunk => { raw += chunk; });
      req.on('end', async () => {
        try {
          const body = JSON.parse(raw);
          const result = await handleAIRequest(body);
          json(res, result, result.error ? 400 : 200);
        } catch (e) {
          json(res, { error: e.message }, 400);
        }
      });
    } catch (e) {
      json(res, { error: e.message }, 500);
    }
    return;
  }

  // 404
  json(res, { error: 'Not found' }, 404);
});

server.listen(PORT, '0.0.0.0', () => {
  console.log('AI Proxy Server running on http://0.0.0.0:' + PORT);
  console.log('Routes: POST /api/ai/generate | GET /health');
});
