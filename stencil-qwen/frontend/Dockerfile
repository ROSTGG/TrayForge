# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./

# Install with increased timeout and network retry
RUN npm install --legacy-peer-deps --network-timeout 60000 || npm install --force

COPY src ./src
COPY index.html vite.config.js ./
RUN npm run build

# Serve stage
FROM nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built frontend from builder
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
