// API Route: POST /api/vision
// Receives base64 image, forwards to Ollama MiniCPM-v, returns description

export async function POST(request: Request) {
  try {
    const { image } = await request.json();
    
    // Strip data:image prefix
    const base64 = image.replace(/^data:image\/\w+;base64,/, '');
    
    const ollamaResp = await fetch('http://localhost:11434/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'minicpm-v:latest',
        prompt: '请用中文简洁描述你在这张照片里看到了什么。3-4句话。包括：人物在做什么、环境、光线。',
        images: [base64],
        stream: false,
      }),
    });

    if (ollamaResp.ok) {
      const data = await ollamaResp.json();
      return Response.json({ description: data.response });
    } else {
      return Response.json({ error: 'Ollama not available' }, { status: 502 });
    }
  } catch (err) {
    return Response.json({ error: 'Vision service unavailable' }, { status: 503 });
  }
}
