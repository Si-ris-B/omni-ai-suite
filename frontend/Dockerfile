# Stage 1: Build the React app using Node
# Use a specific Node LTS version on Alpine for smaller size
FROM node:18-alpine as builder

WORKDIR /app

# Set NODE_ENV to production for optimized build
ENV NODE_ENV=production

# Copy dependency definition files first for caching
COPY frontend/package.json frontend/package-lock.json* ./
# Use npm ci for deterministic installs based on lock file
RUN npm ci --only=production

# Copy the rest of the application code
COPY frontend/ .

# Run the build script defined in package.json
RUN npm run build

# Stage 2: Serve using Nginx from a lightweight base image
FROM nginx:stable-alpine

# Remove default Nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy the custom Nginx configuration from the frontend directory
COPY frontend/nginx.conf /etc/nginx/conf.d/omnicore.conf

# Copy built static files from the builder stage to Nginx's web root
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80 for Nginx (standard HTTP port)
EXPOSE 80

# Start Nginx and keep it running in the foreground
CMD ["nginx", "-g", "daemon off;"]
