/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",          // static site in ./out — no server needed for a demo
  trailingSlash: true,       // /brands/ -> out/brands/index.html (works on any static host)
  images: { unoptimized: true },
  reactStrictMode: true,
};
export default nextConfig;
