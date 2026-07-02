/**
 * fanqie-novel CORS Proxy + AI Router
 * Deploy to Cloudflare Workers (free tier: 100k req/day)
 *
 * Routes:
 *   GET  /?url=...            - CORS proxy for fanqienovel APIs (existing)
 *   POST /api/ai/analyze      - AI style analysis proxy
 *   POST /api/ai/generate     - AI novel generation proxy
 */

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': '*',
  'Access-Control-Max-Age': '86400',
};

export default {
  async fetch(request) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: CORS });
    }

    const url = new URL(request.url);

    // AI routes
    if (request.method === 'POST' && url.pathname === '/api/ai/analyze') {
      return handleAI(request, 'analyze');
    }
    if (request.method === 'POST' && url.pathname === '/api/ai/generate') {
      return handleAI(request, 'generate');
    }

    // Existing CORS proxy
    const target = url.searchParams.get('url');
    if (!target) return new Response('Missing url param', { status: 400, headers: CORS });

    return proxyRequest(target);
  }
};

/**
 * Handle AI API proxy (forward to user's model provider)
 */
async function handleAI(request, type) {
  try {
    const body = await request.json();
    const { endpoint, apiKey, model, messages, options } = body;

    if (!endpoint || !apiKey || !model || !messages) {
      return new Response(JSON.stringify({ error: 'Missing required fields: endpoint, apiKey, model, messages' }), {
        status: 400,
        headers: { ...CORS, 'Content-Type': 'application/json' },
      });
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

    const text = await resp.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      return new Response(JSON.stringify({ error: 'AI API returned non-JSON: ' + text.slice(0, 200) }), {
        status: 502,
        headers: { ...CORS, 'Content-Type': 'application/json' },
      });
    }

    if (!resp.ok) {
      return new Response(JSON.stringify({ error: data.error || ('HTTP ' + resp.status), detail: data }), {
        status: resp.status,
        headers: { ...CORS, 'Content-Type': 'application/json' },
      });
    }

    // Extract content from OpenAI-compatible response
    const content = (data.choices && data.choices[0] && data.choices[0].message)
      ? data.choices[0].message.content
      : '';

    return new Response(JSON.stringify({ content: content, usage: data.usage }), {
      status: 200,
      headers: { ...CORS, 'Content-Type': 'application/json' },
    });

  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), {
      status: 500,
      headers: { ...CORS, 'Content-Type': 'application/json' },
    });
  }
}

/**
 * CORS proxy for fanqienovel APIs (original behavior)
 */
async function proxyRequest(target) {
  let parsed;
  try { parsed = new URL(target); } catch {
    return new Response('Invalid url', { status: 400, headers: CORS });
  }

  const allowedHosts = ['novel.snssdk.com', 'fanqienovel.com', '101.35.133.34'];
  if (!allowedHosts.some(h => parsed.hostname.endsWith(h))) {
    return new Response('Host not allowed', { status: 403, headers: CORS });
  }

  const headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
  };
  if (parsed.hostname !== '101.35.133.34') {
    headers['Referer'] = 'https://fanqienovel.com/';
  }

  const resp = await fetch(target, { headers });

  return new Response(resp.body, {
    status: resp.status,
    headers: {
      ...CORS,
      'Content-Type': resp.headers.get('Content-Type') || 'application/json',
      'Cache-Control': 'public, max-age=300',
    },
  });
}
