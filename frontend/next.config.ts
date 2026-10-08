import type { NextConfig } from "next";
const config: NextConfig = { turbopack: { root: process.cwd() }, output: "export", trailingSlash: true, images: { unoptimized: true } };
export default config;
