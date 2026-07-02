import type { Config } from "@netlify/functions";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export default async (req: Request) => {
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

  const response = await fetch(`${backendUrl.replace(/\/$/, "")}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: await req.text(),
  });

  return new Response(await response.text(), {
    status: response.status,
    headers: {
      ...corsHeaders,
      "Content-Type": "application/json",
    },
  });
};

export const config: Config = {
  path: "/api/analyze",
};
