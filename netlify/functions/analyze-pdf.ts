import type { Config } from "@netlify/functions";
import { proxyToBackend } from "./proxyToBackend";

export default async (req: Request) => proxyToBackend(req, "/api/analyze/pdf");

export const config: Config = {
  path: "/api/analyze/pdf",
};
