# ---- Base image ----
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy app source
COPY . .

# Expose the dev server port
EXPOSE 3000

# Default command: Start Next.js in development mode, listen on all interfaces
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]
