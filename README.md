# ShortNExact

[![License:  MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED? logo=docker&logoColor=white)](https://www.docker.com/)

We've all been there… it's midnight, your essay's due, and the word limit is 500.  You ask ChatGPT to concise it, and it spits out 490… or 512.  Then you waste half an hour going back and forth trying to hit the exact count.

That's exactly why I built **ShortNExact** 👉 an agentic AI tool that trims or expands your text to hit the **exact word count** you need. No more stress, no more guesswork.

Just plug in your OpenAI key, paste your text, and boom — deadline saved 🙌. 

---

## 🌟 Features

- **Exact Word Count Matching**: Uses an intelligent LLM orchestrator to iteratively adjust text until the precise word count is achieved
- **Two Processing Modes**:
  - **Concisely Present Ideas**: Aggressively condense large texts while preserving key concepts
  - **Shorten Text**: Gently reduce word count with minimal structural changes
- **Agentic AI Architecture**: Autonomous tool selection and execution using OpenAI function calling
- **Scalable Backend**: HAProxy load balancing with multiple FastAPI instances
- **Rate Limiting**: Redis-based rate limiting to prevent abuse
- **API Key Management**: PostgreSQL-backed authentication system with time-limited keys
- **Modern UI**: Clean Gradio interface for easy interaction
- **Production-Ready**: Dockerized microservices with health checks and auto-restart

---

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │  (Gradio UI on port 80/443)
│  (Gradio)   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   HAProxy   │  (Load Balancer on port 4000)
│     (LB)    │
└──────┬──────┘
       │
       ├──────────┬──────────┐
       ▼          ▼          ▼
   ┌─────┐   ┌─────┐   ┌─────┐
   │API-1│   │API-2│   │API-3│  (FastAPI instances)
   └──┬──┘   └──┬──┘   └──┬──┘
      │         │         │
      └─────────┼─────────┘
                │
       ┌────────┴────────┐
       ▼                 ▼
  ┌─────────┐      ┌──────────┐
  │  Redis  │      │ Postgres │
  │ (Cache) │      │   (DB)   │
  └─────────┘      └──────────┘
```

---

## 🚀 Getting Started

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



## 📖 Usage

### Web Interface

1. **Generate an API Key** (first-time users):
   - Navigate to the API Key Generation tab
   - Enter your name, email, and desired validity period (max 31 days)
   - Save your generated key

2. **Process Your Text**:
   - Enter your OpenAI API key
   - Paste your ShortNExact app key (generated in step 1)
   - Input your text
   - Set your target word count
   - Select processing mode: 
     - **Concisely present ideas**: For aggressive summarization
     - **Shorten text**: For gentle reduction
   - Click submit and get your perfectly sized text! 

### API Endpoints

#### Main Processing Endpoint
```bash
curl -X GET http://localhost:4000/ \
  -H "Content-Type: application/json" \
  -H "ip_address: YOUR_IP" \
  -d '{
    "llm_api_key": "YOUR_OPENAI_KEY",
    "app_key": "YOUR_APP_KEY",
    "option": 1,
    "input_text": "Your text here.. .",
    "no_of_words": 500
  }'
```

#### API Key Generation
```bash
curl -X GET http://localhost:4000/api_key \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: YOUR_IP" \
  -d '{
    "name": "Your Name",
    "email": "your.email@example.com",
    "validity": 30
  }'
```

---

## 🔧 Technical Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | Gradio |
| **Backend API** | FastAPI |
| **Load Balancer** | HAProxy |
| **Database** | PostgreSQL |
| **Cache** | Redis |
| **LLM Provider** | OpenAI API |
| **NLP** | NLTK |
| **Containerization** | Docker & Docker Compose |

---

## 📁 Project Structure

```
ShortNExact/
├── api. py                    # FastAPI backend with rate limiting
├── ml_layer.py              # LLM orchestrator and agentic processing
├── frontend. py              # Gradio UI components
├── compose.yml              # Docker Compose configuration
├── haproxy.cfg              # Load balancer configuration
├── init. sql                 # Database schema initialization
├── start.sh                 # Build and deployment script
├── Dockerfile. api           # API service container
├── Dockerfile.frontend      # Frontend service container
├── Dockerfile.lb            # Load balancer container
├── api_requirements.txt     # Python dependencies for API
├── frontend_requirements.txt # Python dependencies for frontend
└── README.md
```

---

## 🧠 How It Works

ShortNExact uses an **agentic LLM orchestrator** that: 

1. **Analyzes** the current word count vs. target
2. **Selects** the appropriate tool: 
   - `process_concisely`: Aggressive restructuring
   - `process_short`: Gentle trimming
   - `increase_words`: Expand content
   - `decrease_words`: Minor reduction
3. **Executes** the selected tool via OpenAI function calling
4. **Iterates** until the exact word count is achieved

The system uses regex-based word counting with Unicode support for accurate results across languages.

---

## 🛡️ Rate Limiting & Security

- **Redis-based rate limiting**:  10,000 API key generations per 24 hours
- **IP-based tracking**: Prevents abuse from single sources
- **Time-limited API keys**: Maximum 31-day validity
- **Health checks**: All services monitored with automatic restart
- **Database persistence**: PostgreSQL with volume mounting

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- OpenAI for the powerful GPT models
- The open-source community for the amazing tools
- All contributors who help improve this project

---

## ⭐ Show Your Support

If this project helped you, please consider giving it a star!  It helps others discover the tool. 

[![GitHub stars](https://img.shields.io/github/stars/AdiistheGoat/ShortNExact?style=social)](https://github.com/AdiistheGoat/ShortNExact/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/AdiistheGoat/ShortNExact?style=social)](https://github.com/AdiistheGoat/ShortNExact/network/members)









