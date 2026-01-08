# Docker Orchestrator

A self-service platform for automated deployment of Docker containers with automatic DNS configuration and reverse proxy setup.

## ✨ Recent Updates

- 🌓 **Dark/Light Mode**: Toggle between themes with persistent preference
- ✅ **Smart Validation**: Real-time input validation with duplicate detection
- 🔄 **Progress Tracking**: Live modal showing each creation step with spinners
- 🎯 **Auto-correction**: Type `IP:PORT` format to auto-fill both fields
- 🗑️ **Safe Deletion**: Type-to-confirm mechanism for deleting resources
- 🔍 **Search & Filter**: Find resources quickly in NPM hosts and DNS records
- 🚫 **Smart Submit**: Button disabled until all fields are valid

## Features

### Core Functionality
- **Docker Container Management**: Automatically deploy Docker containers with dedicated networks
- **Automatic DNS Configuration**: Create DNS records via OVH API (A and CNAME records)
- **Reverse Proxy Setup**: Configure Nginx Proxy Manager automatically
- **SSL Certificates**: Optional Let's Encrypt SSL certificates via NPM
- **Subnet Management**: Automatic allocation of isolated subnets for each service

### User Interface
- **Modern Web Interface**: Clean, intuitive form-based interface
- **Dark/Light Mode**: Toggle between day and night themes with persistent preference
- **Real-time Validation**:
  - Input validation with visual feedback (green/red borders)
  - Auto-correction for IP:PORT format (extracts and fills both fields)
  - Duplicate detection for subdomains (checks DNS and NPM)
  - Smart button state (disabled until all fields are valid)
- **Progress Tracking**:
  - Live progress modal showing each creation step
  - Animated spinner for operations in progress
  - Visual status indicators (pending, in-progress, success, error)
- **Resource Management**:
  - View all DNS records from OVH
  - View all NPM proxy hosts
  - Delete records/hosts with mandatory confirmation (type-to-confirm)
  - Search/filter functionality for hosts and records

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

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM
- **SQLite**: Lightweight database for tracking services
- **Python Docker SDK**: Container management
- **OVH Python SDK**: DNS record management
- **Requests**: HTTP client for NPM API

### Frontend
- **Vanilla JavaScript**: No framework dependencies for fast loading
- **CSS Variables**: Dynamic theming support
- **LocalStorage API**: Persistent user preferences
- **Fetch API**: Modern async HTTP requests
- **CSS Grid/Flexbox**: Responsive layout

### Features Implementation
- **Real-time validation**: Debounced input handlers (800ms)
- **Theme switching**: CSS class toggle with localStorage persistence
- **Progress tracking**: Modal-based step visualization
- **Delete confirmation**: Type-to-confirm security pattern
- **Caching**: 1-minute cache for API responses to reduce load

## Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd Docker-to-NPM
cp .env.example .env

# Edit .env with your credentials
nano .env

# Start the application
docker-compose up -d

# Access the interface
# Frontend: http://localhost:8080
# API Docs: http://localhost:8000/docs
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

### Creating DNS Records and Proxy Hosts

1. **Open the web interface** at http://localhost:8080

2. **Toggle dark mode** (optional): Click the ☀️/🌙 button in the top-right corner

3. **Fill in the form** with smart validation:
   - **Subdomain**: Enter subdomain name (e.g., `my-app`)
     - Auto-validates format and checks for duplicates
     - Shows ✓ if available or ⚠️ if already exists
   - **Create DNS CNAME**: Toggle if you want to create DNS record
   - **CNAME Target**: Target for DNS (@ for root domain)
   - **TTL**: Time-to-live for DNS record
   - **Target Host/IP**: Enter IP or hostname
     - Supports `192.168.1.100:8080` format (auto-fills port)
     - Validates IPv4 and hostname formats
     - Shows ✓ for valid entries
   - **Target Port**: Port number (1-65535)
     - Auto-filled if entered with host
     - Shows common port types (HTTP, HTTPS, etc.)
   - **Enable SSL**: Toggle Let's Encrypt SSL certificate

4. **Create**: Button activates only when all fields are valid
   - Watch progress modal with live status updates
   - Each step shows spinner → checkmark/error

### Managing Resources

#### Viewing Resources
- **System Status**: Collapsible section showing Docker, NPM, and OVH health
- **NPM Proxy Hosts**: Lists all configured reverse proxy hosts
  - Domain, forward target, SSL status, creation date
  - Search/filter by domain or target
- **DNS Records**: Shows all OVH DNS records (A and CNAME)
  - Type, subdomain, target, TTL
  - Search/filter by any field

#### Deleting Resources

1. Click **Delete** button on any DNS record or NPM host
2. Confirmation modal appears with:
   - Warning that action cannot be undone
   - Name of resource to delete (in red)
3. **Type exact name** to confirm (e.g., `myapp` or `@`)
4. **Delete Permanently** button activates when typed correctly
5. Resource is deleted and lists refresh automatically

### API Endpoints

#### Health & Info
- `GET /` - API info and documentation links
- `GET /health` - System health check (Docker, NPM, OVH status)

#### DNS & Proxy Management
- `POST /api/dns-proxy` - Create DNS record + NPM proxy host
- `GET /api/dns/records` - List all DNS records
- `DELETE /api/dns/records/{record_id}` - Delete DNS record
- `GET /api/npm/hosts` - List all NPM proxy hosts
- `DELETE /api/npm/hosts/{proxy_host_id}` - Delete NPM host

#### Full Service Management (Docker + DNS + NPM)
- `POST /api/services` - Create complete service with container
- `GET /api/services` - List all services
- `DELETE /api/services/{service_name}` - Delete service with cleanup

See full API documentation at http://localhost:8000/docs

## Examples

### Smart Input Validation

**Scenario 1: Quick IP:Port Entry**
```
You type: 192.168.1.100:8080
Result:
  - Host field: 192.168.1.100 ✅
  - Port field: 8080 ✅ (HTTP Alternate)
  - Both fields auto-validated
```

**Scenario 2: Duplicate Detection**
```
You type subdomain: myapp
Result:
  - Checks DNS records...
  - Checks NPM hosts...
  - ⚠️ Subdomain already exists!
    DNS: CNAME record exists (→ @)
    NPM: Proxy host exists (→ 192.168.1.100:80)
  - Submit button stays disabled
```

**Scenario 3: Valid New Entry**
```
Subdomain: newapp ✅ Subdomain available
Host: 10.0.0.50 ✅ Valid IPv4 address
Port: 3000 ✅ Valid port (Development)
→ Submit button activates
```

### Safe Deletion Flow

**Deleting DNS Record:**
```
1. Click "Delete" on "myapp" DNS record
2. Modal appears:
   ⚠️ Confirm Deletion
   This will permanently delete: myapp

3. Type "myapp" in confirmation field
4. Button "Delete Permanently" activates
5. Click → Record deleted → Lists refresh
```

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

### Validation issues in browser

- Clear browser cache and reload (Ctrl+F5 / Cmd+Shift+R)
- Check browser console for JavaScript errors (F12)
- Ensure API is running and accessible at `http://localhost:8000`
- Try in incognito/private mode to rule out extension conflicts

### Theme not persisting

- Check browser allows localStorage (some privacy modes disable it)
- Clear localStorage and reload: `localStorage.clear()` in browser console

## Browser Compatibility

- **Chrome/Edge**: ✅ Fully supported (v90+)
- **Firefox**: ✅ Fully supported (v88+)
- **Safari**: ✅ Fully supported (v14+)
- **Mobile browsers**: ✅ Responsive design works on all modern mobile browsers

**Required features:**
- CSS Variables (custom properties)
- ES6+ JavaScript (async/await, arrow functions)
- Fetch API
- LocalStorage API

## UI Features

### Form Validation
- **Real-time validation** with visual feedback (green/red borders)
- **Smart input handling**:
  - Type `192.168.1.100:8080` → auto-extracts IP and port
  - Validates IPv4, hostnames, and port ranges
  - Common port detection (shows "HTTP", "HTTPS", etc.)
- **Duplicate detection**: Checks if subdomain already exists in DNS or NPM
- **Disabled submit** until all fields are valid with tooltip showing missing fields

### Progress Tracking
- **Live progress modal** appears during creation
- **Visual steps** with status indicators:
  - ⏳ Pending (gray)
  - 🔄 In Progress (blue spinner)
  - ✅ Success (green)
  - ❌ Error (red)
- Steps shown: DNS creation → NPM host → SSL configuration

### Theme Support
- **Light/Dark mode toggle** in header (☀️/🌙 button)
- Theme persists across sessions (localStorage)
- All UI elements adapt to theme

### Resource Management
- **Collapsible sections** for System Status, NPM Hosts, DNS Records
- **Search/filter** functionality on all lists
- **Delete with confirmation**: Type-to-confirm safety mechanism

## Security Considerations

- The orchestrator needs access to Docker socket (high privileges)
- **Delete confirmation** requires typing exact resource name
- Input validation prevents injection attacks
- Secure the web interface (add authentication)
- Use HTTPS for the orchestrator interface in production
- Restrict access to the API
- Store `.env` securely (never commit to git)

## Future Enhancements

- [ ] Authentication on web interface (OAuth, JWT)
- [ ] Service templates (Nextcloud, Gitea, WordPress, etc.)
- [ ] Multi-server support (deploy across multiple hosts)
- [ ] Service health monitoring (uptime, response time)
- [ ] Automatic backups and snapshots
- [ ] Resource limits configuration (CPU, memory)
- [ ] Custom domain support (not just subdomains)
- [ ] Bulk operations (delete multiple, export configs)
- [ ] Activity logs and audit trail
- [ ] Webhook notifications (Discord, Slack)

## License

MIT

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
