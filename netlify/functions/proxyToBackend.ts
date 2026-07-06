const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export async function proxyToBackend(req: Request, backendPath: string): Promise<Response> {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  if (req.method !== "POST") {
    return Response.json({ detail: "Method not allowed" }, { status: 405, headers: corsHeaders });
  }

  const backendUrl = process.env.BACKEND_URL;
  if (!backendUrl) {
    return Response.json(
      { detail: "API 서버가 설정되지 않았습니다. BACKEND_URL 환경 변수를 확인하세요." },
      { status: 503, headers: corsHeaders },
    );
  }

  const contentType = req.headers.get("content-type");
  const headers: Record<string, string> = {};
  if (contentType) {
    headers["Content-Type"] = contentType;
  }

  const response = await fetch(`${backendUrl.replace(/\/$/, "")}${backendPath}`, {
    method: "POST",
    headers,
    body: await req.arrayBuffer(),
  });

  return new Response(await response.text(), {
    status: response.status,
    headers: {
      ...corsHeaders,
      "Content-Type": response.headers.get("content-type") ?? "application/json",
    },
  });
}
