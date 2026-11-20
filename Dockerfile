# 1) Node собирает Vite-бандл и baking'ит nginx-конфиг с адресом бэкенда
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN node scripts/bake-rewrites.mjs
RUN npm run build

# 2) nginx раздаёт статику и проксирует /api/* на бэкенд
FROM nginx:1.27-alpine
COPY --from=build /app/nginx.conf.generated.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
ENV PORT=8080
# ОБЯЗАТЕЛЬНО: envsubst в официальном образе подставляет только PORT,
# иначе затрёт переменные самого nginx ($uri, $proxy_host, ...).
ENV NGINX_ENVSUBST_FILTER=PORT
EXPOSE 8080
