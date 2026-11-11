FROM node:22-slim
RUN corepack enable
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile --prod
COPY src ./src
ENV PORT=3001
EXPOSE 3001
CMD ["sh", "-c", "node src/seed.js && exec node src/index.js"]
