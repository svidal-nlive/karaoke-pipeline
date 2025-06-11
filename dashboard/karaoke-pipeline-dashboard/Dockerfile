# ---- Build stage ----
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps
COPY . .
RUN npm run build

# ---- Production Nginx stage ----
FROM nginx:1.25-alpine
WORKDIR /usr/share/nginx/html
COPY --from=build /app/build .
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Set envsubst in entrypoint to inject REACT_APP_STATUS_API_URL at runtime if desired
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
