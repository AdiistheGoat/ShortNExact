
docker compose down
docker system prune
docker build -f Dockerfile.frontend -t frontend_img .
docker build -f Dockerfile.lb -t lb_img .
docker build -f Dockerfile.api -t api_img .
docker compose up -d 
