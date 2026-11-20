import { existsSync, readFileSync } from "node:fs";
import type { NextConfig } from "next";

/**
 * Адрес бэкенда. Источник — rewrites.json (единая точка правды), значение
 * зашивается в образ на сборке. Переопределение через BACKEND_URL возможно,
 * но в панели RelaxDev его задавать не нужно.
 */
function backendUrl(): string {
  const fromEnv = process.env["BACKEND_URL"];
  if (fromEnv && /^https?:\/\//i.test(fromEnv)) {
    return fromEnv.replace(/\/$/, "");
  }
  if (existsSync("rewrites.json")) {
    const cfg = JSON.parse(readFileSync("rewrites.json", "utf8"));
    const api = cfg.rewrites?.find(
      (r: { source?: string }) => typeof r.source === "string" && r.source.includes("/api"),
    );
    if (api?.destination) {
      return String(api.destination).replace(/\/$/, "");
    }
  }
  return "https://conference-agenda-back.relaxdev.ru";
}

const backend = backendUrl();

const nextConfig: NextConfig = {
  // RelaxDev: автосборка ищет .next/standalone → нужен именно standalone-сервер,
  // который сам слушает PORT и проксирует /api/* через rewrites ниже.
  output: "standalone",
  // Прокси /api/* → бэкенд (путь сохраняется: /api/... → <backend>/api/...).
  // Работает в standalone-режиме (в export — не работал бы).
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${backend}/api/:path*` }];
  },
};

export default nextConfig;
