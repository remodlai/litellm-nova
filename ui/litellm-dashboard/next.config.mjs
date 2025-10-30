/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  basePath: "",
  assetPrefix: "/litellm-asset-prefix", // If a server_root_path is set, this will be overridden by runtime injection
  images: {
    unoptimized: true,
  },
  eslint: {
    ignoreDuringBuilds: true,  // Skip linting during build
  },
  typescript: {
    ignoreBuildErrors: true,  // Skip type checking during build
  },
};

nextConfig.experimental = {
  missingSuspenseWithCSRBailout: false,
};

export default nextConfig;
