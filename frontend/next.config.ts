import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Avoid Next.js writing its own AGENTS.md/CLAUDE.md into frontend/ on every
  // `next dev` -- this repo has a single project-wide constitution at the
  // repo root (../CLAUDE.md).
  agentRules: false,
  // Smaller, self-contained production image for Docker.
  output: "standalone",
};

export default nextConfig;
