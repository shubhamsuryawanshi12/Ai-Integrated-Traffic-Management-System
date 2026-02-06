FROM node:18-alpine

WORKDIR /app

COPY package.json .

# We don't copy package-lock.json yet as it might not exist or be synced yet
# But usually we should.
# For now, we'll install deps if they aren't there, or better, rely on the volume for dev.
# But to build the image we need to install.

RUN npm install

COPY . .

CMD ["npm", "start"]
