import type { NextConfig } from "next";

// Turbopack désactivé : une politique Windows Application Control bloque le
// binding natif @next/swc-win32-x64-msvc sur cette machine, et Turbopack
// n'a pas de repli WASM (contrairement au compilateur Webpack classique).
// Voir package.json ("dev"/"build" passent --webpack).
const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "www.sofascore.com",
        pathname: "/api/v1/**",
      },
    ],
  },
};

export default nextConfig;
