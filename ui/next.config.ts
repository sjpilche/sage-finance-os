import type { NextConfig } from "next";

const backendUrl = process.env.BACKEND_URL || "http://localhost:8090";

const nextConfig: NextConfig = {
  // Proxy API calls to the FastAPI backend
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
