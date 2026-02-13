FROM node:20-alpine AS base
RUN apk add --no-cache python3 make g++ git

WORKDIR /app

# ── Stage 1: Install Medusa ──────────────────────────────────
FROM base AS installer

# Clone official Medusa starter and install dependencies
RUN git clone --depth 1 https://github.com/medusajs/medusa-starter-default.git medusa-backend \
    && cd medusa-backend \
    && rm -rf .git \
    && npm install --legacy-peer-deps

# ── Stage 2: Production image ────────────────────────────────
FROM node:20-alpine AS production
RUN apk add --no-cache tini curl

WORKDIR /app/medusa

# Copy installed Medusa app
COPY --from=installer /app/medusa-backend/ ./

# Expose Medusa API + Admin
EXPOSE 9000 7001

# Health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=5 \
  CMD curl -f http://localhost:9000/health || exit 1

# Use tini as init process
ENTRYPOINT ["/sbin/tini", "--"]

# Default: start Medusa server
CMD ["sh", "-c", "npx medusa migrations run && npm run start"]
