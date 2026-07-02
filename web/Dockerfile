FROM node:20-alpine AS build
WORKDIR /app/web
COPY web/package.json web/package-lock.json* ./
RUN npm install
COPY web/ .
COPY infra/keycloak/themes/acom-offerdesk/login/resources/css /app/infra/keycloak/themes/acom-offerdesk/login/resources/css
RUN npm run build

FROM nginx:1.27-alpine
COPY web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/web/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
