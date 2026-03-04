FROM node:20-alpine

WORKDIR /app

COPY apps/web/package.json apps/web/pnpm-lock.yaml* ./
RUN corepack enable && pnpm install --frozen-lockfile 2>/dev/null || pnpm install

COPY apps/web/ ./

EXPOSE 3002

CMD ["pnpm", "dev"]
