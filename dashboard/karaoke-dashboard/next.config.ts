/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'rorecclesia.com',
        port: '',
        pathname: '/demo/wp-content/uploads/**',
      },
    ],
  },
  // Remove experimental.allowedDevOrigins for now
};

export default nextConfig;
