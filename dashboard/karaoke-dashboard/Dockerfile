FROM node:20-alpine

# 1. Ensure directory exists and is owned by root (will adjust later)
RUN mkdir -p /home/node/app

WORKDIR /home/node/app

# 2. Copy package files as root, install dependencies
COPY package*.json ./
RUN npm install

# 3. Adjust ownership so the node user can write
RUN chown -R node:node /home/node/app

# 4. Switch to unprivileged user
USER node

# 5. Copy the rest of your app as node
COPY --chown=node:node . .

EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]
