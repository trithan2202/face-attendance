# Stage 1: Build the React application
FROM node:18-alpine as build
WORKDIR /app

# Copy package.json and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the application source code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:alpine

# Copy custom nginx configuration for React Router
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the build output to replace the default nginx contents.
# Vite builds to 'dist' directory by default.
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Run nginx
CMD ["nginx", "-g", "daemon off;"]
