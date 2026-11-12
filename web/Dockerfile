FROM node:22-alpine AS build
WORKDIR /app/web
COPY web/package.json web/package-lock.json* ./
COPY web/scripts/copy-pdf-assets.mjs ./scripts/copy-pdf-assets.mjs
RUN npm install
COPY web/ .
COPY shared/fonts /app/shared/fonts
RUN npm run build

FROM nginx:1.27-alpine
COPY web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/web/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
