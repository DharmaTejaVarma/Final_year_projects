# ==============================================================================
# TravelSenseAI — Frontend Multi-Stage Production Dockerfile
# Stage 1: Build React/Vite SPA
# Stage 2: Serve via Nginx Alpine
# ==============================================================================

# ---- Stage 1: Build ----
FROM node:20-alpine as builder

WORKDIR /app

# Copy dependency manifests
COPY package.json package-lock.json* ./

# Install npm dependencies
RUN npm install --legacy-peer-deps

# Copy application source files
COPY . .

# Build production distribution
RUN npm run build

# ---- Stage 2: Production Nginx Server ----
FROM nginx:alpine as runner

# Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy built artifacts from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose HTTP port
EXPOSE 80

# Health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

# Start Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]

