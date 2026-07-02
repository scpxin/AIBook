/**
 * Laf.dev 云函数 - AI 代理
 * 
 * 部署到 https://laf.dev 后替换前端中的 AI_PROXY_URL 变量
 * 
 * 部署步骤:
 * 1. 打开 https://laf.dev 注册/登录
 * 2. 创建应用 → 进入云函数页面
 * 3. 新建函数，命名为 ai-proxy
 * 4. 将此文件内容粘贴进去，点击发布
 * 5. 获取函数调用地址，填入 docs/index.html 中的 AI_PROXY 变量
 */

import cloud from '@lafjs/cloud'

export default async function (ctx: FunctionContext) {
  // 允许跨域
  ctx.response.set('Access-Control-Allow-Origin', '*')
  ctx.response.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  ctx.response.set('Access-Control-Allow-Headers', '*')

  if (ctx.method === 'OPTIONS') {
    return { code: 0 }
  }

  // 仅接受 POST
  if (ctx.method !== 'POST') {
    return { error: '仅支持 POST 请求' }
  }

  const { endpoint, apiKey, model, messages, options } = ctx.body || {}

  // 参数校验
  if (!endpoint || !apiKey || !model || !messages) {
    return { error: '缺少必填字段: endpoint, apiKey, model, messages' }
  }

  try {
    const reqBody = {
      model: model,
      messages: messages,
      temperature: (options && options.temperature) || 0.7,
      max_tokens: (options && options.max_tokens) || 4096,
    }

    console.log('Request to:', endpoint, 'Model:', model)

    const resp = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + apiKey,
      },
      body: JSON.stringify(reqBody),
    })

    const data = await resp.json()

    if (!resp.ok) {
      console.error('AI API error:', data)
      return { error: data.error && data.error.message ? data.error.message : ('HTTP ' + resp.status) }
    }

    // 提取 OpenAI 兼容格式的返回内容
    const content = (data.choices && data.choices[0] && data.choices[0].message)
      ? data.choices[0].message.content
      : ''

    return {
      content: content,
      usage: data.usage || null,
    }

  } catch (e) {
    console.error('Proxy error:', e.message)
    return { error: '代理请求失败: ' + e.message }
  }
}
