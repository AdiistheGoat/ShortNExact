# ShortNExact


## Cloning the repo 

### 1. Clone the repository

```sh
git clone https://github.com/AdiistheGoat/ShortNExact
cd ShortNExact
```

### 2. Create and activate a virtual environment

```sh
python3 -m venv venv
source ./venv/bin/activate
```

### 4. Run starting script

```sh
bash start.sh
```

## Running with Docker Images from Docker Hub

### 1. **Ensure you have the following files in your project directory.**
   ```sh
haproxy.cfg
init.sql
pgbouncer.ini 
compose.yml 
userlist.txt 
   ```

### 2. **Pull the pre-built images from Docker Hub:**
   ```sh
docker pull adityagoyal333/short_n_exact:api_img
docker pull adityagoyal333/short_n_exact:lb_img
docker pull adityagoyal333/short_n_exact:frontend_img
   ```
### 3. **Change the tag names of the image**
   ```sh
docker tag adityagoyal333/short_n_exact:api_img api_img:latest
docker tag adityagoyal333/short_n_exact:lb_img  lb_img:latest
docker tag adityagoyal333/short_n_exact:frontend_img frontend_img:latest
   ```

### 3. **Start all services using Docker Compose:**
   ```sh
docker compose down
docker system prune
docker compose up -d
   ```
---

