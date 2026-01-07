# Docker Orchestrator

A self-service platform for automated deployment of Docker containers with automatic DNS configuration and reverse proxy setup.

## Features

- **Docker Container Management**: Automatically deploy Docker containers with dedicated networks
- **Automatic DNS Configuration**: Create DNS records via OVH API
- **Reverse Proxy Setup**: Configure Nginx Proxy Manager automatically
- **SSL Certificates**: Optional Let's Encrypt SSL certificates via NPM
- **Subnet Management**: Automatic allocation of isolated subnets for each service
- **Web Interface**: User-friendly form for service deployment

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Interface Web (Form)                   │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                   API Backend (FastAPI)                  │
│  - Validation des inputs                                 │
│  - Orchestration des appels                              │
└──────┬──────────────┬──────────────────┬────────────────┘
       │              │                  │
       ▼              ▼                  ▼
┌────────────┐  ┌───────────┐  ┌─────────────────┐
│  Docker    │  │    NPM    │  │   OVH API       │
│  Engine    │  │    API    │  │   (DNS)         │
└────────────┘  └───────────┘  └─────────────────┘
```

## Project Structure

```
Docker-to-NPM/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic models
│   ├── database.py          # SQLAlchemy setup
│   ├── services/
│   │   ├── docker_service.py    # Docker operations
│   │   ├── npm_service.py       # NPM API client
│   │   ├── ovh_service.py       # OVH DNS client
│   │   └── subnet_manager.py    # Subnet allocation
│   └── requirements.txt
├── frontend/
│   ├── index.html           # Web interface
│   ├── style.css            # Styling
│   └── app.js               # Frontend logic
├── docker-compose.yml       # Deployment configuration
├── Dockerfile               # Backend container
├── nginx.conf               # Frontend web server config
├── .env.example             # Environment variables template
└── README.md
```

## Prerequisites

- Docker and Docker Compose
- Access to Docker socket (for container management)
- Nginx Proxy Manager running and accessible
- OVH API credentials
- A domain configured in OVH

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd Docker-to-NPM
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and configure:

- **OVH API credentials** (from https://api.ovh.com/createToken/)
- **NPM connection** (URL, email, password)
- **Server public IP** (for DNS A records)
- **Network configuration** (subnet pool and size)

### 3. Install dependencies (for local development)

```bash
cd backend
pip install -r requirements.txt
```

### 4. Run with Docker Compose

```bash
docker-compose up -d
```

The application will be available at:
- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Usage

### Creating a Service

1. Open the web interface at http://localhost:8080
2. Fill in the form:
   - **Service Name**: lowercase letters, numbers, and hyphens (e.g., `my-app`)
   - **Docker Image**: full image name with tag (e.g., `nginx:latest`)
   - **Internal Port**: port where your app listens inside the container
   - **Environment Variables** (optional): one per line, format `KEY=value`
   - **Volumes** (optional): one per line, format `/host/path:/container/path`
   - **Enable SSL**: check to enable Let's Encrypt SSL certificate
3. Click "Create Service"

The system will automatically:
1. Allocate a dedicated subnet
2. Create a Docker network
3. Deploy the container
4. Create DNS A record (subdomain.yourdomain.tld → server IP)
5. Configure NPM proxy host (with SSL if enabled)

### Managing Services

- View all deployed services in the right panel
- Click "Delete" to remove a service (cleans up all resources)

### API Endpoints

- `GET /health` - System health check
- `POST /api/services` - Create a new service
- `GET /api/services` - List all services
- `DELETE /api/services/{service_name}` - Delete a service

See full API documentation at http://localhost:8000/docs

## Development

### Run backend locally

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Run frontend locally

Serve the frontend directory with any web server, for example:

```bash
cd frontend
python -m http.server 8080
```

Update `API_URL` in `frontend/app.js` to point to your backend.

## Configuration Details

### OVH API Setup

1. Go to https://api.ovh.com/createToken/
2. Select your endpoint (ovh-eu)
3. Grant permissions:
   - GET /domain/zone/*
   - POST /domain/zone/*
   - DELETE /domain/zone/*
4. Copy the credentials to your `.env` file

### Nginx Proxy Manager

- NPM must be running and accessible
- Use admin credentials (email + password)
- The orchestrator will authenticate via the NPM API

### Network Configuration

By default, the orchestrator uses:
- **Subnet Pool**: `172.20.0.0/16`
- **Subnet Size**: `/24` (256 addresses per service)

Each service gets its own `/24` subnet, e.g.:
- Service 1: `172.20.0.0/24`
- Service 2: `172.20.1.0/24`
- etc.

## Troubleshooting

### Docker connection failed

- Ensure Docker socket is accessible: `ls -la /var/run/docker.sock`
- Check `DOCKER_HOST` in `.env`

### NPM authentication failed

- Verify NPM URL is correct and accessible
- Check NPM credentials in `.env`
- Test manually: `curl http://npm-url/api/schema`

### OVH API errors

- Verify credentials are correct
- Check API token hasn't expired
- Test with: `python -c "import ovh; c = ovh.Client(); print(c.get('/me'))"`

### DNS not propagating

- DNS changes can take time (up to 24h, usually faster)
- Check record was created in OVH control panel
- SSL certificates won't work until DNS propagates

## Security Considerations

- The orchestrator needs access to Docker socket (high privileges)
- Secure the web interface (add authentication)
- Use HTTPS for the orchestrator interface in production
- Restrict access to the API
- Store `.env` securely (never commit to git)

## Future Enhancements

- [ ] Authentication on web interface
- [ ] Service templates (Nextcloud, Gitea, etc.)
- [ ] Multi-server support
- [ ] Service health monitoring
- [ ] Automatic backups
- [ ] Resource limits (CPU, memory)
- [ ] Custom domain support (not just subdomains)

## License

MIT

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
