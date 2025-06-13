# ---- Build stage ----
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files first for caching
COPY package.json package-lock.json ./

# Upgrade npm first for stable builds
RUN npm install -g npm@11.4.2

# Retry npm ci up to 5 times on failure, with legacy-peer-deps flag
RUN set -eux; \
    n=0; \
    until [ $n -ge 5 ]; do \
      npm ci --legacy-peer-deps && break; \
      n=$((n+1)); \
      echo "npm ci failed, retrying ($n/5)..."; \
      sleep 5; \
    done

# Copy the rest of your source code
COPY . .

# Run build
RUN npm run build

# ---- Production Nginx stage ----
FROM nginx:1.25-alpine

WORKDIR /usr/share/nginx/html

COPY --from=build /app/build .

COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 for HTTP
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
