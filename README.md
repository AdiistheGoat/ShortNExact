# ShortNExact


## Cloning the repo 

### 1. Clone the repository

```sh
git clone https://github.com/AdiistheGoat/ShortNExact
cd llm_project
```

### 2. Create and activate a virtual environment

```sh
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```sh
pip3 install -r requirements.txt
```

### 4. Build Docker images

```sh
docker build -f Dockerfile.api -t api_img .
docker build -f Dockerfile.frontend -t frontend_img .
```

### 5. Start services with Docker Compose

```sh
docker compose up
```

## Running with Docker Images from Docker Hub

### 1. **Ensure you have `compose.yml` and `init.sql` in your project directory.**

### 2. **Pull the pre-built images from Docker Hub:**
   ```sh
   docker pull frontend_img
   docker pull backend_img
   ```

### 3. **Start all services using Docker Compose:**
   ```sh
   docker compose up
   ```

---

