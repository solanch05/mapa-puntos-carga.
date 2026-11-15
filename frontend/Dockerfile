# 1) Compilar la PWA
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
# Instalamos sin el lockfile para esquivar un bug de npm con las dependencias
# opcionales nativas (rolldown/vite): https://github.com/npm/cli/issues/4828
RUN rm -f package-lock.json && npm install --no-audit --no-fund
COPY . .
RUN npm run build

# 2) Servirla con nginx, que además reenvía /api y /admin al backend
FROM nginx:1.29-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80