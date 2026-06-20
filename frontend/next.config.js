/** @type {import('next').NextConfig} */
const nextConfig = {
  // Next 15 infers the workspace root from the nearest lockfile upward; an
  // unrelated package-lock.json in the user's home directory (outside this
  // repo) was being picked up instead. Pin it explicitly to this project.
  outputFileTracingRoot: __dirname,
};

module.exports = nextConfig;
