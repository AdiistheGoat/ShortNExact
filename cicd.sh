docker buildx create --name mybuilder --use
docker buildx inspect --bootstrap

docker buildx build --platform linux/amd64 -f Dockerfile.frontend -t frontend_img --load .
docker buildx build --platform linux/amd64 -f Dockerfile.lb -t lb_img --load .
docker buildx build --platform linux/amd64 -f Dockerfile.api -t api_img --load .

docker tag frontend_img:latest adityagoyal333/short_n_exact:frontend_img
docker tag lb_img:latest adityagoyal333/short_n_exact:lb_img
docker tag api_img:latest adityagoyal333/short_n_exact:api_img

docker push adityagoyal333/short_n_exact:frontend_img
docker push adityagoyal333/short_n_exact:lb_img
docker push adityagoyal333/short_n_exact:api_img

scp /Users/adityagoyal/Desktop/ShortNExact/haproxy.cfg adityagoyal@35.209.29.92:/home/agoyal33/short_and_exact
scp /Users/adityagoyal/Desktop/ShortNExact/init.sql adityagoyal@35.209.29.92:/home/agoyal33/short_and_exact
scp /Users/adityagoyal/Desktop/ShortNExact/pgbouncer.ini adityagoyal@35.209.29.92:/home/agoyal33/short_and_exact
scp /Users/adityagoyal/Desktop/ShortNExact/compose.yml adityagoyal@35.209.29.92:/home/agoyal33/short_and_exact
scp /Users/adityagoyal/Desktop/ShortNExact/userlist.txt adityagoyal@35.209.29.92:/home/agoyal33/short_and_exact
