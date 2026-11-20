# 1) Node собирает Next.js (output: "standalone" → .next/standalone/server.js)
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# 2) Запускаем standalone-сервер: он сам слушает PORT и проксирует /api/* на бэкенд
FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
# Next standalone server.js читает HOSTNAME/PORT.
# HOSTNAME=0.0.0.0 обязателен в контейнере, иначе bind падает на hostname контейнера.
ENV HOSTNAME=0.0.0.0
ENV PORT=8080
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
EXPOSE 8080
CMD ["node", "server.js"]
