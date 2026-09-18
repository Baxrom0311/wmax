FROM nginx:1.27-alpine

RUN rm -rf /etc/nginx/conf.d/*

COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/default.conf /etc/nginx/conf.d/default.conf

RUN mkdir -p /var/www/certbot /var/log/nginx && \
    touch /var/log/nginx/access.log /var/log/nginx/error.log

EXPOSE 80 443

HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
