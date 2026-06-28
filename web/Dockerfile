# node:20-alpine had critical CVEs (CVE-2024-27983, CVE-2024-22019 et al.)
# node:22-alpine uses Node 22 LTS on Alpine 3.22 — all patches applied
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json ./
RUN npm install --frozen-lockfile

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
