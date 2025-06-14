# syntax=docker/dockerfile:1.4
# ——— Build Stage ———
FROM node:20-alpine AS build
WORKDIR /app

# copy just lockfiles first so npm cache can persist across rebuilds
COPY package.json package-lock.json ./

# cache npm downloads
RUN --mount=type=cache,target=/root/.npm \
    npm ci --legacy-peer-deps

# copy the rest of your source
COPY . .

# now build, reusing the npm cache but NOT overriding node_modules
RUN --mount=type=cache,target=/root/.npm \
    npm run build

# ——— Production Nginx Stage ———
FROM nginx:1.25-alpine AS production
WORKDIR /usr/share/nginx/html

# copy only the built assets
COPY --from=build /app/build ./

# your custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
