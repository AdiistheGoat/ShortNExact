docker system prune
pip3 freeze > requirements.txt 
docker build -f Dockerfile.api -t api_img .
docker compose up -d 
