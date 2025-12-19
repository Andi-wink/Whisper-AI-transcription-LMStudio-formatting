import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Disable React Strict Mode to prevent double-mounting issues with LiveKit connections
  reactStrictMode: false,
};

export default nextConfig;
