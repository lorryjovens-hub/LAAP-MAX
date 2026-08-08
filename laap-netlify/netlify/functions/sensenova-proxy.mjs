// ---- LAAP SenseNova 生产代理 ----
// 将 /api/sensenova/v1/* 转发到 https://token.sensenova.cn/v1/*，
// 并在服务端注入 Authorization，避免前端暴露 API Key。
// 需要环境变量 SENSENOVA_API_KEY。

const TARGET = 'https://token.sensenova.cn';
const TOKEN = process.env.SENSENOVA_API_KEY;

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  };
}

export default async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: corsHeaders() });
  }

  if (!TOKEN) {
    return new Response(
      JSON.stringify({ error: 'SenseNova API Key 未在服务端配置' }),
      { status: 500, headers: { 'Content-Type': 'application/json', ...corsHeaders() } }
    );
  }

  const url = new URL(req.url);
  const targetPath = url.pathname.replace(/^\/api\/sensenova/, '/v1') + url.search;
  const targetUrl = `${TARGET}${targetPath}`;

  const headers = {};
  for (const [key, value] of req.headers.entries()) {
    const lower = key.toLowerCase();
    if (lower === 'host' || lower === 'authorization' || lower === 'content-length') continue;
    headers[key] = value;
  }
  headers.Authorization = `Bearer ${TOKEN}`;

  try {
    const response = await fetch(targetUrl, {
      method: req.method,
      headers,
      body: req.body,
      duplex: 'half',
    });

    const responseHeaders = {};
    response.headers.forEach((value, key) => {
      if (key.toLowerCase() === 'content-encoding') return;
      responseHeaders[key] = value;
    });

    return new Response(response.body, {
      status: response.status,
      headers: { ...responseHeaders, ...corsHeaders() },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({ error: err.message || 'SenseNova 代理请求失败' }),
      { status: 502, headers: { 'Content-Type': 'application/json', ...corsHeaders() } }
    );
  }
};
