# =============================================================================
# 天府一网监 前端 + Nginx Dockerfile
# 多阶段构建：构建阶段 (Node) → 运行阶段 (Nginx)
# =============================================================================

# ---- Stage 1: Builder ----
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first for layer caching
COPY package.json ./
COPY package-lock.json* yarn.lock* pnpm-lock.yaml* ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build static assets
RUN npm run build

# ---- Stage 2: Runtime ----
FROM nginx:alpine

# Copy built static files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
