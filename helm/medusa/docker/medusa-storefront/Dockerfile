FROM node:20-alpine AS base
RUN apk add --no-cache python3 make g++ git

WORKDIR /app

# ── Stage 1: Install storefront ──────────────────────────────
FROM base AS installer

# Clone the official Medusa Next.js starter and install deps
RUN git clone --depth 1 https://github.com/medusajs/nextjs-starter-medusa.git storefront \
    && cd storefront \
    && rm -rf .git \
    && npm install --legacy-peer-deps

# ── Stage 2: Production image ────────────────────────────────
FROM node:20-alpine AS production
RUN apk add --no-cache tini curl

WORKDIR /app/storefront

# Copy installed storefront
COPY --from=installer /app/storefront/ ./

# Build will happen at runtime with correct env vars
# (NEXT_PUBLIC_MEDUSA_BACKEND_URL must be set at build time for Next.js)
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=90s --retries=5 \
  CMD curl -f http://localhost:8000/ || exit 1

ENTRYPOINT ["/sbin/tini", "--"]

# Build + start at runtime so NEXT_PUBLIC_ env vars are baked in
CMD ["sh", "-c", "npm run build && npm run start"]
