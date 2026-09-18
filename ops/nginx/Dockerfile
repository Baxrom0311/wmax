FROM nginx:1.27-alpine

# Remove default configuration files
RUN rm -rf /etc/nginx/conf.d/*

# Copy custom configurations
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/nazorat.conf /etc/nginx/conf.d/default.conf

# Create directory for certbot challenges and logs
RUN mkdir -p /var/www/certbot /var/log/nginx && \
    touch /var/log/nginx/access.log /var/log/nginx/error.log

EXPOSE 80 443

HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
