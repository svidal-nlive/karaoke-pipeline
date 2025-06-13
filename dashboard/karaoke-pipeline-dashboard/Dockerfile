# ---- Build stage ----
# Use Debian slim for faster, more reliable CRA builds
# Requires BuildKit: export DOCKER_BUILDKIT=1
FROM node:20-slim AS build
WORKDIR /app

# Install curl (needed only if you ever fetch anything)
RUN apt-get update \
 && apt-get install -y curl \
 && rm -rf /var/lib/apt/lists/*

# Copy only lockfiles first — leverages layer caching
COPY package.json package-lock.json ./

# Cache npm modules between builds
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Copy the rest of your source
COPY . .

# Do the heavy CRA build
RUN npm run build

# ---- Production Nginx stage ----
FROM nginx:1.25-alpine AS production
WORKDIR /usr/share/nginx/html

# Copy only your static build artifacts
COPY --from=build /app/build .  

# Use your custom nginx.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
