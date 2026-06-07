/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Build enxuto pro container (web.Dockerfile copia .next/standalone).
  output: 'standalone',
};

module.exports = nextConfig;
