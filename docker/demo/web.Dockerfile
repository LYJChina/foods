FROM node:20-bookworm-slim

WORKDIR /app
COPY frontend/web/package.json frontend/web/package-lock.json ./
RUN npm install --legacy-peer-deps --no-audit --no-fund
COPY frontend/web/ ./

EXPOSE 5180
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5180"]
