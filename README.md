# Docker Orchestrator

A self-service platform for automated deployment of Docker containers with automatic DNS configuration and reverse proxy setup.

## 🎉 What's New in v2.0

**Major Configuration Overhaul:**
- 🎛️ **Database-Driven Configuration**: NPM and DNS settings now stored in SQLite database
- 🌐 **Multi-Provider DNS Support**: Choose between OVH and Cloudflare (more coming soon!)
- ⚙️ **Admin Web Interface**: Manage all configurations through a clean, tabbed UI
- 🔄 **Hot-Reload Config**: Changes take effect immediately without restart
- 📖 **Guided Setup**: Step-by-step instructions with auto-generated API credential links
- 🔐 **Secure Credential Storage**: Masked secrets with show/hide toggles

**Migration from v1.x:**
- Existing `.env` credentials are automatically migrated to database on first startup
- Infrastructure settings (Docker, network) remain in `.env` file
- No breaking changes - everything still works!

## ✨ All Features

- ⚙️ **Admin Configuration Interface**: Manage NPM and DNS settings via web UI
- 🔄 **Multi-Provider DNS**: Support for both OVH and Cloudflare DNS providers
- 💾 **Database-Driven Config**: NPM/DNS settings stored in database (no .env editing needed)
- 📋 **Guided Setup**: Step-by-step instructions with auto-generated API credential links
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
- **Multi-Provider DNS**: Support for **OVH** and **Cloudflare** DNS providers (A and CNAME records)
- **Reverse Proxy Setup**: Configure Nginx Proxy Manager automatically
- **SSL Certificates**: Optional Let's Encrypt SSL certificates via NPM
- **Subnet Management**: Automatic allocation of isolated subnets for each service
- **Web-Based Configuration**: Manage NPM and DNS provider settings via admin interface

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
  - View all DNS records from configured provider (OVH/Cloudflare)
  - View all NPM proxy hosts
  - Delete records/hosts with mandatory confirmation (type-to-confirm)
  - Search/filter functionality for hosts and records
- **Admin Configuration Interface**:
  - Manage NPM connection settings (URL, credentials)
  - Switch between OVH and Cloudflare DNS providers
  - Update API credentials without editing files
  - Guided setup with auto-generated credential links

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Web Interface + Admin Panel                 │
│  - Service deployment forms                              │
│  - NPM & DNS configuration management                    │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              API Backend (FastAPI + SQLite)              │
│  - Input validation & orchestration                      │
│  - Database-driven configuration                         │
│  - Multi-provider DNS abstraction                        │
└──────┬──────────────┬──────────────────┬────────────────┘
       │              │                  │
       ▼              ▼                  ▼
┌────────────┐  ┌───────────┐  ┌──────────────────────┐
│  Docker    │  │    NPM    │  │   DNS Providers      │
│  Engine    │  │    API    │  │  - OVH API           │
│            │  │           │  │  - Cloudflare API    │
└────────────┘  └───────────┘  └──────────────────────┘
```

## Project Structure

```
Docker-to-NPM/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic models
│   ├── database.py          # SQLAlchemy setup + config storage
│   ├── services/
│   │   ├── docker_service.py       # Docker operations
│   │   ├── npm_service.py          # NPM API client
│   │   ├── ovh_service.py          # OVH DNS client
│   │   ├── cloudflare_service.py   # Cloudflare DNS client
│   │   └── subnet_manager.py       # Subnet allocation
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
- **SQLAlchemy**: Database ORM for service tracking and configuration storage
- **SQLite**: Lightweight database for services, NPM config, and DNS config
- **Python Docker SDK**: Container management
- **OVH Python SDK**: DNS record management for OVH
- **Cloudflare API**: DNS record management via REST API
- **Requests**: HTTP client for NPM and Cloudflare APIs

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
git clone https://github.com/xguitoux/Docker-to-NPM
cd Docker-to-NPM
cp .env.example .env

# Edit .env with infrastructure settings (Docker, network, etc.)
nano .env

# Start the application
docker-compose up -d

# Access the web interface and configure NPM + DNS provider
# Frontend: http://localhost:8080
# 1. Click the ⚙️ Admin button
# 2. Configure NPM settings (URL, credentials)
# 3. Configure DNS provider (OVH or Cloudflare)
# 4. Check system status - all should be green!

# API Docs: http://localhost:8000/docs
```

**Note**: First-time users should configure NPM and DNS via the web admin interface. If you have existing settings in `.env`, they will be automatically migrated to the database on first startup.

## Prerequisites

- Docker and Docker Compose
- Access to Docker socket (for container management)
- Nginx Proxy Manager running and accessible
- DNS Provider (choose one):
  - **OVH**: API credentials from https://api.ovh.com/createToken/
  - **Cloudflare**: API token and Zone ID from https://dash.cloudflare.com/
- A domain configured with your chosen DNS provider

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

Edit `.env` and configure **infrastructure settings**:

- **Server public IP** (for DNS A records)
- **Docker socket path** (default: unix:///var/run/docker.sock)
- **Network configuration** (subnet pool and size)
- **Database URL** (default: SQLite)

**Note**: NPM and DNS provider credentials are now managed via the **Admin Interface** in the web UI (no need to edit .env for these).

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

### Initial Setup: Configure NPM and DNS Provider

**On first launch, configure your NPM and DNS settings:**

1. **Open the web interface** at http://localhost:8080

2. **Click the ⚙️ Admin button** in the top-right corner

3. **NPM Configuration Tab**:
   - Enter your NPM URL (e.g., `http://npm.example.com:81`)
   - Enter admin email and password
   - Click "Save NPM Config"

4. **DNS Provider Tab**:
   - Select your DNS provider (OVH or Cloudflare)

   **For OVH**:
   - Enter your zone name (e.g., `example.com`)
   - The interface will generate a custom link with pre-filled permissions
   - Click the link to create your API credentials
   - Copy Application Key, Application Secret, and Consumer Key
   - Paste them in the form and save

   **For Cloudflare**:
   - Follow the step-by-step guide in the interface
   - Get your Zone ID from the Cloudflare dashboard
   - Create an API token with "Edit zone DNS" permission
   - Enter both values and save

5. **Check system status** to verify all connections are working (green indicators)

### Creating DNS Records and Proxy Hosts

1. **Toggle dark mode** (optional): Click the ☀️/🌙 button in the top-right corner

2. **Fill in the form** with smart validation:
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
- **System Status**: Collapsible section showing Docker, NPM, and DNS Provider health
  - Shows currently configured DNS provider (OVH or Cloudflare)
- **NPM Proxy Hosts**: Lists all configured reverse proxy hosts
  - Domain, forward target, SSL status, creation date
  - Search/filter by domain or target
- **DNS Records**: Shows all DNS records from your configured provider (A and CNAME)
  - Type, subdomain, target, TTL, zone name
  - Search/filter by any field
  - Works with both OVH and Cloudflare

#### Deleting Resources

1. Click **Delete** button on any DNS record or NPM host
2. Confirmation modal appears with:
   - Warning that action cannot be undone
   - Name of resource to delete (in red)
3. **Type exact name** to confirm (e.g., `myapp` or `@`)
4. **Delete Permanently** button activates when typed correctly
5. Resource is deleted and lists refresh automatically

#### Changing DNS Provider

You can switch between OVH and Cloudflare at any time:

1. Click the **⚙️ Admin button**
2. Go to the **DNS Provider tab**
3. Select the new provider (OVH or Cloudflare)
4. Enter the required credentials for the new provider
5. Click **Save DNS Config**
6. The system status will update to show the new provider
7. All future DNS operations will use the new provider

**Note**: Existing DNS records remain with the original provider. Only new records will be created with the newly selected provider.

### API Endpoints

#### Health & Info
- `GET /` - API info and documentation links
- `GET /health` - System health check (Docker, NPM, DNS provider status)

#### DNS & Proxy Management
- `POST /api/dns-proxy` - Create DNS record + NPM proxy host
- `GET /api/dns/records` - List all DNS records (from configured provider)
- `DELETE /api/dns/records/{record_id}` - Delete DNS record
- `GET /api/npm/hosts` - List all NPM proxy hosts
- `DELETE /api/npm/hosts/{proxy_host_id}` - Delete NPM host

#### Full Service Management (Docker + DNS + NPM)
- `POST /api/services` - Create complete service with container
- `GET /api/services` - List all services
- `DELETE /api/services/{service_name}` - Delete service with cleanup

#### Admin Configuration (New)
- `GET /api/admin/npm-config` - Get current NPM configuration
- `PUT /api/admin/npm-config` - Update NPM configuration
- `GET /api/admin/dns-config` - Get current DNS provider configuration
- `PUT /api/admin/dns-config` - Update DNS provider and credentials

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

### Managing Configuration

**NPM and DNS credentials are managed via the web interface** (Admin panel). On first startup, the system will:

1. Read initial values from `.env` file (if present)
2. Store them in the SQLite database
3. All future configuration changes happen through the web UI
4. No need to restart the application after config changes

### DNS Provider Setup

#### OVH API Credentials

**Easiest method - Use the admin interface:**
1. Open Admin panel → DNS Provider tab
2. Enter your zone name (e.g., `example.com`)
3. Click the auto-generated link
4. The OVH page will have permissions pre-filled:
   - `GET /domain/zone/{your-zone}/*`
   - `POST /domain/zone/{your-zone}/*`
   - `DELETE /domain/zone/{your-zone}/*`
5. Create the token and paste the 3 credentials back

**Manual method:**
1. Go to https://api.ovh.com/createToken/
2. Select endpoint (ovh-eu, ovh-ca, or ovh-us)
3. Grant permissions for `/domain/zone/{your-zone}/*`
4. Enter credentials in Admin panel

#### Cloudflare API Credentials

**Using the admin interface:**
1. Open Admin panel → DNS Provider tab
2. Follow the step-by-step instructions shown
3. Get Zone ID from Cloudflare dashboard overview
4. Create API token with "Edit zone DNS" template
5. Enter both values and save

**Token permissions required:**
- Zone / DNS / Edit

### Nginx Proxy Manager

Configure via Admin panel → NPM Configuration tab:
- NPM URL (e.g., `http://npm.example.com:81`)
- Admin email and password
- Connection is tested when you save

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

- Check system status indicator in the web UI (should be green)
- Verify NPM URL is correct and accessible
- Update credentials via Admin panel → NPM Configuration
- Test manually: `curl http://npm-url/api/schema`

### DNS Provider errors

**For OVH:**
- Check system status indicator (shows "DNS Provider (OVH)")
- Verify credentials in Admin panel → DNS Provider
- Check API token hasn't expired
- Ensure zone name matches your OVH domain
- Test with: `python -c "import ovh; c = ovh.Client(); print(c.get('/me'))"`

**For Cloudflare:**
- Check system status indicator (shows "DNS Provider (CLOUDFLARE)")
- Verify API token has "Edit zone DNS" permission
- Ensure Zone ID is correct (found on Cloudflare dashboard)
- Test token with: `curl -X GET "https://api.cloudflare.com/client/v4/zones/{zone_id}" -H "Authorization: Bearer {token}"`

### Configuration not taking effect

- Configuration is stored in database (`orchestrator.db`)
- Changes via Admin panel take effect immediately (no restart needed)
- Check browser console for errors (F12)

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

### Admin Configuration Interface
- **Tabbed interface** for NPM and DNS settings
- **Password masking** with show/hide toggles
- **Real-time configuration updates** (no restart required)
- **Guided setup** with step-by-step instructions:
  - OVH: Auto-generated credential links with pre-filled permissions
  - Cloudflare: Detailed walkthrough with direct links to dashboard
- **Visual feedback** on save with success/error messages
- **Dynamic UI** that adapts to selected DNS provider

## Security Considerations

- The orchestrator needs access to Docker socket (high privileges)
- **Delete confirmation** requires typing exact resource name
- Input validation prevents injection attacks
- Secure the web interface (add authentication)
- Use HTTPS for the orchestrator interface in production
- Restrict access to the API
- Store `.env` securely (never commit to git)

## Future Enhancements

- [ ] Authentication on web interface (OAuth, JWT, basic auth)
- [ ] Additional DNS providers (Google Cloud DNS, AWS Route53, etc.)
- [ ] Service templates (Nextcloud, Gitea, WordPress, etc.)
- [ ] Multi-server support (deploy across multiple hosts)
- [ ] Service health monitoring (uptime, response time)
- [ ] Automatic backups and snapshots
- [ ] Resource limits configuration (CPU, memory)
- [ ] Custom domain support (not just subdomains)
- [ ] Bulk operations (delete multiple, export configs, import)
- [ ] Activity logs and audit trail
- [ ] Webhook notifications (Discord, Slack, email)
- [ ] Configuration backup/restore
- [ ] NPM SSL certificate management
- [ ] Container logs viewer

## License

MIT

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
