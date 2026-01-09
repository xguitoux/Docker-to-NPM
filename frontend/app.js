// API Configuration
const API_URL = 'http://localhost:8000';

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    checkHealth();
    loadNPMHosts();
    loadDNSRecords();
    setupFormHandler();
    setupToggleButtons();
    setupInputValidation();
    setupDeleteModal();
    setupAdminModal();

    // Refresh NPM hosts and DNS records every 30 seconds
    setInterval(() => {
        loadNPMHosts();
        loadDNSRecords();
    }, 30000);
});

// Cache for DNS records and NPM hosts
let cachedDNSRecords = [];
let cachedNPMHosts = [];
let cacheTimestamp = 0;
const CACHE_DURATION = 60000; // 1 minute

// Delete modal state
let deleteModalState = {
    type: null, // 'dns' or 'npm'
    id: null,
    name: null,
    callback: null
};

// Setup delete confirmation modal
function setupDeleteModal() {
    const modal = document.getElementById('deleteModal');
    const confirmInput = document.getElementById('deleteConfirmInput');
    const confirmBtn = document.getElementById('deleteConfirmBtn');
    const cancelBtn = document.getElementById('deleteCancelBtn');

    // Validate input and enable/disable confirm button
    confirmInput.addEventListener('input', () => {
        const inputValue = confirmInput.value.trim();
        const requiredValue = deleteModalState.name;

        if (inputValue === requiredValue) {
            confirmBtn.disabled = false;
            confirmInput.classList.add('match');
        } else {
            confirmBtn.disabled = true;
            confirmInput.classList.remove('match');
        }
    });

    // Cancel button
    cancelBtn.addEventListener('click', () => {
        closeDeleteModal();
    });

    // Confirm delete button
    confirmBtn.addEventListener('click', async () => {
        confirmBtn.disabled = true;
        confirmBtn.textContent = 'Deleting...';

        try {
            if (deleteModalState.type === 'dns') {
                await deleteDNSRecord(deleteModalState.id);
            } else if (deleteModalState.type === 'npm') {
                await deleteNPMHost(deleteModalState.id);
            }

            closeDeleteModal();

            // Invalidate cache and reload
            cacheTimestamp = 0;
            setTimeout(() => {
                loadNPMHosts();
                loadDNSRecords();
            }, 500);

        } catch (error) {
            console.error('Delete error:', error);
            alert('Failed to delete: ' + error.message);
            confirmBtn.disabled = false;
            confirmBtn.textContent = 'Delete Permanently';
        }
    });

    // Close modal on overlay click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeDeleteModal();
        }
    });
}

// Show delete confirmation modal
function showDeleteModal(type, id, name) {
    const modal = document.getElementById('deleteModal');
    const targetElement = document.getElementById('deleteTarget');
    const requiredTextElement = document.getElementById('deleteRequiredText');
    const confirmInput = document.getElementById('deleteConfirmInput');
    const confirmBtn = document.getElementById('deleteConfirmBtn');

    // Store state
    deleteModalState = { type, id, name };

    // Update modal content
    targetElement.textContent = name;
    requiredTextElement.textContent = name;

    // Reset input
    confirmInput.value = '';
    confirmInput.classList.remove('match');
    confirmBtn.disabled = true;
    confirmBtn.textContent = 'Delete Permanently';

    // Show modal
    modal.classList.add('active');

    // Focus input
    setTimeout(() => confirmInput.focus(), 100);
}

// Close delete confirmation modal
function closeDeleteModal() {
    const modal = document.getElementById('deleteModal');
    modal.classList.remove('active');
    deleteModalState = { type: null, id: null, name: null };
}

// Delete DNS record
async function deleteDNSRecord(recordId) {
    const response = await fetch(`${API_URL}/api/dns/records/${recordId}`, {
        method: 'DELETE'
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete DNS record');
    }

    return await response.json();
}

// Delete NPM host
async function deleteNPMHost(hostId) {
    const response = await fetch(`${API_URL}/api/npm/hosts/${hostId}`, {
        method: 'DELETE'
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete NPM host');
    }

    return await response.json();
}

// Load existing DNS records and NPM hosts for validation
async function loadExistingRecordsForValidation() {
    const now = Date.now();

    // Return cached data if still fresh
    if (cacheTimestamp && (now - cacheTimestamp) < CACHE_DURATION) {
        return { dns: cachedDNSRecords, npm: cachedNPMHosts };
    }

    try {
        const [dnsResponse, npmResponse] = await Promise.all([
            fetch(`${API_URL}/api/dns/records`).catch(() => ({ ok: false })),
            fetch(`${API_URL}/api/npm/hosts`).catch(() => ({ ok: false }))
        ]);

        if (dnsResponse.ok) {
            const dnsData = await dnsResponse.json();
            cachedDNSRecords = dnsData.success ? dnsData.records : [];
        }

        if (npmResponse.ok) {
            const npmData = await npmResponse.json();
            cachedNPMHosts = npmData.success ? npmData.hosts : [];
        }

        cacheTimestamp = now;
    } catch (error) {
        console.error('Error loading records for validation:', error);
    }

    return { dns: cachedDNSRecords, npm: cachedNPMHosts };
}

// Input Validation and Auto-correction
function setupInputValidation() {
    const subdomainInput = document.getElementById('subdomain');
    const subdomainFeedback = document.getElementById('subdomainFeedback');
    const targetHostInput = document.getElementById('targetHost');
    const targetPortInput = document.getElementById('targetPort');
    const targetHostFeedback = document.getElementById('targetHostFeedback');
    const targetPortFeedback = document.getElementById('targetPortFeedback');
    const submitBtn = document.querySelector('#dnsProxyForm button[type="submit"]');

    // Validation state tracker
    const validationState = {
        subdomain: false,
        targetHost: false,
        targetPort: false
    };

    // Check if form is valid and update submit button
    function updateSubmitButton() {
        const isFormValid = validationState.subdomain &&
                           validationState.targetHost &&
                           validationState.targetPort;

        const validationHint = document.getElementById('formValidationHint');

        if (submitBtn) {
            submitBtn.disabled = !isFormValid;
            if (!isFormValid) {
                submitBtn.style.opacity = '0.5';
                submitBtn.style.cursor = 'not-allowed';

                // Show validation hint
                if (validationHint) {
                    validationHint.classList.add('show');
                }

                // Build detailed tooltip message
                const missingFields = [];
                if (!validationState.subdomain) missingFields.push('Subdomain');
                if (!validationState.targetHost) missingFields.push('Target Host/IP');
                if (!validationState.targetPort) missingFields.push('Target Port');

                if (missingFields.length > 0) {
                    submitBtn.title = `Please validate: ${missingFields.join(', ')}`;
                } else {
                    submitBtn.title = 'Please fill all required fields correctly';
                }
            } else {
                submitBtn.style.opacity = '1';
                submitBtn.style.cursor = 'pointer';
                submitBtn.title = 'All fields are valid - Click to create';

                // Hide validation hint
                if (validationHint) {
                    validationHint.classList.remove('show');
                }
            }
        }
    }

    // Validate subdomain format and check for duplicates
    async function validateSubdomain() {
        const value = subdomainInput.value.trim().toLowerCase();

        if (!value) {
            subdomainInput.classList.remove('valid', 'invalid');
            hideFeedback(subdomainFeedback);
            validationState.subdomain = false;
            updateSubmitButton();
            return;
        }

        // Validate format first
        const subdomainPattern = /^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$/;
        if (!subdomainPattern.test(value)) {
            subdomainInput.classList.add('invalid');
            subdomainInput.classList.remove('valid');
            showFeedback(subdomainFeedback, '✗ Only lowercase letters, numbers, and hyphens allowed', 'error');
            validationState.subdomain = false;
            updateSubmitButton();
            return;
        }

        // Check for existing records
        showFeedback(subdomainFeedback, 'Checking for duplicates...', 'info');
        const { dns, npm } = await loadExistingRecordsForValidation();

        let warnings = [];

        // Check DNS records
        const existingDNS = dns.find(record => {
            const subdomain = record.subdomain === '@' ? '' : record.subdomain;
            return subdomain.toLowerCase() === value;
        });

        if (existingDNS) {
            warnings.push(`DNS: ${existingDNS.type} record exists (→ ${existingDNS.target})`);
        }

        // Check NPM hosts
        const existingNPM = npm.find(host => {
            if (!host.domain_names || host.domain_names.length === 0) return false;
            // Extract subdomain from full domain (e.g., "myapp.domain.com" -> "myapp")
            const fullDomain = host.domain_names[0];
            const subdomain = fullDomain.split('.')[0];
            return subdomain.toLowerCase() === value;
        });

        if (existingNPM) {
            const forwardTo = `${existingNPM.forward_host}:${existingNPM.forward_port}`;
            warnings.push(`NPM: Proxy host exists (→ ${forwardTo})`);
        }

        if (warnings.length > 0) {
            subdomainInput.classList.add('invalid');
            subdomainInput.classList.remove('valid');
            showFeedback(
                subdomainFeedback,
                `⚠️ Subdomain already exists!\n${warnings.join('\n')}`,
                'error'
            );
            validationState.subdomain = false;
            updateSubmitButton();
        } else {
            subdomainInput.classList.add('valid');
            subdomainInput.classList.remove('invalid');
            showFeedback(subdomainFeedback, '✓ Subdomain available', 'success');
            validationState.subdomain = true;
            updateSubmitButton();
        }
    }

    // Validate IPv4 address
    function isValidIPv4(ip) {
        const ipv4Pattern = /^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
        return ipv4Pattern.test(ip);
    }

    // Validate hostname
    function isValidHostname(hostname) {
        const hostnamePattern = /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
        return hostnamePattern.test(hostname) && hostname.length <= 253;
    }

    // Validate port number
    function isValidPort(port) {
        const portNum = parseInt(port);
        return !isNaN(portNum) && portNum >= 1 && portNum <= 65535;
    }

    // Parse and extract IP:PORT format
    function parseHostPort(input) {
        // Check for IP:PORT or HOSTNAME:PORT format
        const match = input.match(/^(.+):(\d+)$/);
        if (match) {
            return {
                host: match[1].trim(),
                port: match[2]
            };
        }
        return null;
    }

    // Show feedback message
    function showFeedback(feedbackElement, message, type) {
        feedbackElement.textContent = message;
        feedbackElement.className = `input-feedback ${type}`;
    }

    // Hide feedback message
    function hideFeedback(feedbackElement) {
        feedbackElement.className = 'input-feedback';
        feedbackElement.textContent = '';
    }

    // Validate target host input
    function validateTargetHost() {
        const value = targetHostInput.value.trim();

        if (!value) {
            targetHostInput.classList.remove('valid', 'invalid');
            hideFeedback(targetHostFeedback);
            validationState.targetHost = false;
            updateSubmitButton();
            return;
        }

        // Check if input contains port
        const parsed = parseHostPort(value);
        if (parsed) {
            // Extract host and port
            const { host, port } = parsed;

            // Validate host
            if (isValidIPv4(host) || isValidHostname(host)) {
                // Set the host without port
                targetHostInput.value = host;
                targetHostInput.classList.add('valid');
                targetHostInput.classList.remove('invalid');
                showFeedback(targetHostFeedback, `✓ Host corrected. Port ${port} extracted.`, 'success');
                validationState.targetHost = true;

                // Auto-fill port if valid
                if (isValidPort(port)) {
                    targetPortInput.value = port;
                    targetPortInput.classList.add('valid');
                    targetPortInput.classList.remove('invalid');
                    showFeedback(targetPortFeedback, `✓ Port auto-filled: ${port}`, 'success');
                    validationState.targetPort = true;
                }

                // Validate port field after auto-fill
                setTimeout(validateTargetPort, 100);
            } else {
                targetHostInput.classList.add('invalid');
                targetHostInput.classList.remove('valid');
                showFeedback(targetHostFeedback, '✗ Invalid IP or hostname format', 'error');
                validationState.targetHost = false;
                updateSubmitButton();
            }
        } else {
            // No port in input, just validate host
            if (isValidIPv4(value)) {
                targetHostInput.classList.add('valid');
                targetHostInput.classList.remove('invalid');
                showFeedback(targetHostFeedback, '✓ Valid IPv4 address', 'success');
                validationState.targetHost = true;
                updateSubmitButton();
            } else if (isValidHostname(value)) {
                targetHostInput.classList.add('valid');
                targetHostInput.classList.remove('invalid');
                showFeedback(targetHostFeedback, '✓ Valid hostname', 'success');
                validationState.targetHost = true;
                updateSubmitButton();
            } else {
                targetHostInput.classList.add('invalid');
                targetHostInput.classList.remove('valid');
                showFeedback(targetHostFeedback, '✗ Invalid IP address or hostname', 'error');
                validationState.targetHost = false;
                updateSubmitButton();
            }
        }
    }

    // Validate target port input
    function validateTargetPort() {
        const value = targetPortInput.value.trim();

        if (!value) {
            targetPortInput.classList.remove('valid', 'invalid');
            hideFeedback(targetPortFeedback);
            validationState.targetPort = false;
            updateSubmitButton();
            return;
        }

        if (isValidPort(value)) {
            targetPortInput.classList.add('valid');
            targetPortInput.classList.remove('invalid');

            // Show common port info
            const portNum = parseInt(value);
            let portInfo = '✓ Valid port';

            const commonPorts = {
                80: 'HTTP',
                443: 'HTTPS',
                8080: 'HTTP Alternate',
                3000: 'Development',
                5000: 'Flask/Development',
                8000: 'Development',
                8443: 'HTTPS Alternate',
                9000: 'Development'
            };

            if (commonPorts[portNum]) {
                portInfo = `✓ Valid port (${commonPorts[portNum]})`;
            }

            showFeedback(targetPortFeedback, portInfo, 'success');
            validationState.targetPort = true;
            updateSubmitButton();
        } else {
            targetPortInput.classList.add('invalid');
            targetPortInput.classList.remove('valid');
            showFeedback(targetPortFeedback, '✗ Port must be between 1 and 65535', 'error');
            validationState.targetPort = false;
            updateSubmitButton();
        }
    }

    // Attach event listeners
    if (subdomainInput) {
        // Debounce function for subdomain validation
        let subdomainTimeout;
        subdomainInput.addEventListener('input', () => {
            // Clear validation on input
            subdomainInput.classList.remove('valid', 'invalid');
            hideFeedback(subdomainFeedback);
            validationState.subdomain = false;
            updateSubmitButton();

            // Debounce validation (wait 800ms after user stops typing)
            clearTimeout(subdomainTimeout);
            subdomainTimeout = setTimeout(() => {
                validateSubdomain();
            }, 800);
        });

        subdomainInput.addEventListener('blur', () => {
            clearTimeout(subdomainTimeout);
            validateSubdomain();
        });
    }

    if (targetHostInput) {
        targetHostInput.addEventListener('blur', validateTargetHost);
        targetHostInput.addEventListener('input', () => {
            // Clear validation on input
            targetHostInput.classList.remove('valid', 'invalid');
            hideFeedback(targetHostFeedback);
            validationState.targetHost = false;
            updateSubmitButton();
        });
    }

    if (targetPortInput) {
        targetPortInput.addEventListener('blur', validateTargetPort);
        targetPortInput.addEventListener('input', () => {
            // Clear validation on input
            targetPortInput.classList.remove('valid', 'invalid');
            hideFeedback(targetPortFeedback);
            validationState.targetPort = false;
            updateSubmitButton();
        });
    }

    // Initialize button state
    updateSubmitButton();
}

// Theme Management
function initializeTheme() {
    // Check for saved theme preference or default to light mode
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);

    // Setup theme toggle button
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
}

function toggleTheme() {
    const currentTheme = document.body.classList.contains('dark-mode') ? 'dark' : 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    applyTheme(newTheme);
    localStorage.setItem('theme', newTheme);
}

function applyTheme(theme) {
    const body = document.body;
    const themeToggle = document.getElementById('themeToggle');
    const slider = themeToggle?.querySelector('.theme-toggle-slider');

    if (theme === 'dark') {
        body.classList.add('dark-mode');
        themeToggle?.classList.add('dark');
        if (slider) slider.textContent = '🌙';
    } else {
        body.classList.remove('dark-mode');
        themeToggle?.classList.remove('dark');
        if (slider) slider.textContent = '☀️';
    }
}

// Setup toggle buttons for collapsible sections
function setupToggleButtons() {
    // System Status toggle
    const toggleSystemStatus = document.getElementById('toggleSystemStatus');
    const systemStatusContent = document.getElementById('systemStatusContent');

    if (toggleSystemStatus && systemStatusContent) {
        toggleSystemStatus.addEventListener('click', () => {
            toggleSystemStatus.classList.toggle('collapsed');
            systemStatusContent.classList.toggle('collapsed');
        });
    }

    // NPM Hosts toggle
    const toggleNpmHosts = document.getElementById('toggleNpmHosts');
    const npmHostsList = document.getElementById('npmHostsList');

    if (toggleNpmHosts && npmHostsList) {
        toggleNpmHosts.addEventListener('click', () => {
            toggleNpmHosts.classList.toggle('collapsed');
            npmHostsList.classList.toggle('collapsed');
        });
    }

    // DNS Records toggle
    const toggleDnsRecords = document.getElementById('toggleDnsRecords');
    const dnsRecordsList = document.getElementById('dnsRecordsList');

    if (toggleDnsRecords && dnsRecordsList) {
        toggleDnsRecords.addEventListener('click', () => {
            toggleDnsRecords.classList.toggle('collapsed');
            dnsRecordsList.classList.toggle('collapsed');
        });
    }

    // Toggle DNS fields based on checkbox
    const createDNSCheckbox = document.getElementById('createDNS');
    const dnsFields = document.getElementById('dnsFields');

    if (createDNSCheckbox && dnsFields) {
        createDNSCheckbox.addEventListener('change', () => {
            if (createDNSCheckbox.checked) {
                dnsFields.style.display = 'block';
            } else {
                dnsFields.style.display = 'none';
            }
        });
    }

    // Search/filter NPM hosts
    const npmHostsSearch = document.getElementById('npmHostsSearch');
    if (npmHostsSearch) {
        npmHostsSearch.addEventListener('input', (e) => {
            filterNPMHosts(e.target.value.toLowerCase());
        });
    }

    // Search/filter DNS records
    const dnsRecordsSearch = document.getElementById('dnsRecordsSearch');
    if (dnsRecordsSearch) {
        dnsRecordsSearch.addEventListener('input', (e) => {
            filterDNSRecords(e.target.value.toLowerCase());
        });
    }
}

// Check system health
async function checkHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();

        updateStatusIndicator('dockerStatus', data.docker, data.docker_error);
        updateStatusIndicator('npmStatus', data.npm, data.npm_error);
        updateStatusIndicator('ovhStatus', data.ovh, data.ovh_error);

        // Load and display DNS provider
        loadDNSProviderLabel();
    } catch (error) {
        console.error('Health check failed:', error);
        updateStatusIndicator('dockerStatus', false, 'Cannot reach API');
        updateStatusIndicator('npmStatus', false, 'Cannot reach API');
        updateStatusIndicator('ovhStatus', false, 'Cannot reach API');
    }
}

async function loadDNSProviderLabel() {
    try {
        const response = await fetch(`${API_URL}/api/admin/dns-config`);
        if (response.ok) {
            const config = await response.json();
            const label = document.getElementById('dnsProviderLabel');
            if (label) {
                const providerName = config.dns_provider.toUpperCase();
                label.textContent = `DNS Provider (${providerName}):`;
            }
        }
    } catch (error) {
        console.error('Error loading DNS provider label:', error);
    }
}

function updateStatusIndicator(elementId, isHealthy, errorMessage) {
    const element = document.getElementById(elementId);
    element.textContent = isHealthy ? 'OK' : 'Error';
    element.className = `status-value ${isHealthy ? 'healthy' : 'unhealthy'}`;

    // Add title attribute for tooltip with error details
    if (!isHealthy && errorMessage) {
        element.title = errorMessage;
        element.style.cursor = 'help';
    } else {
        element.title = isHealthy ? 'Service is operational' : 'Service unavailable';
        element.style.cursor = 'default';
    }
}

// Load and display NPM hosts
async function loadNPMHosts() {
    const hostsContainer = document.getElementById('npmHostsList');

    try {
        const response = await fetch(`${API_URL}/api/npm/hosts`);
        const data = await response.json();

        if (!data.success || data.hosts.length === 0) {
            hostsContainer.innerHTML = '<p class="empty-state">No proxy hosts configured</p>';
            return;
        }

        hostsContainer.innerHTML = data.hosts.map(host => createNPMHostCard(host)).join('');

        // Update cache with fresh data
        if (data.success) {
            cachedNPMHosts = data.hosts;
        }

    } catch (error) {
        console.error('Failed to load NPM hosts:', error);
        hostsContainer.innerHTML = '<p class="error">Failed to load NPM hosts</p>';
    }
}

function createNPMHostCard(host) {
    const domain = host.domain_names && host.domain_names.length > 0 ? host.domain_names[0] : 'N/A';
    const sslStatus = host.certificate_id ? 'SSL Enabled' : 'No SSL';
    const sslClass = host.certificate_id ? 'active' : 'partial';
    // Escape quotes for onclick attribute
    const escapedDomain = domain.replace(/'/g, "\\'");

    return `
        <div class="service-card">
            <div class="service-header">
                <div class="service-name">${domain}</div>
                <div class="service-status ${sslClass}">${sslStatus}</div>
            </div>
            <div class="service-details">
                <div class="service-detail">
                    <span class="detail-label">Domain:</span>
                    <span class="detail-value">
                        <a href="https://${domain}" target="_blank">${domain}</a>
                    </span>
                </div>
                <div class="service-detail">
                    <span class="detail-label">Forward to:</span>
                    <span class="detail-value">${host.forward_scheme}://${host.forward_host}:${host.forward_port}</span>
                </div>
                <div class="service-detail">
                    <span class="detail-label">Created:</span>
                    <span class="detail-value">${new Date(host.created_on).toLocaleString()}</span>
                </div>
                <div class="service-detail">
                    <span class="detail-label">Status:</span>
                    <span class="detail-value">${host.enabled ? 'Enabled' : 'Disabled'}</span>
                </div>
            </div>
            <div class="service-actions">
                <button class="btn-delete-small" onclick="showDeleteModal('npm', ${host.id}, '${escapedDomain}')">
                    Delete
                </button>
            </div>
        </div>
    `;
}

// Progress Modal Management
let currentSteps = [];

function showProgressModal(steps) {
    currentSteps = steps;
    const modal = document.getElementById('progressModal');
    const stepsContainer = document.getElementById('progressSteps');
    const closeBtn = document.getElementById('closeModal');

    // Reset modal
    stepsContainer.innerHTML = '';
    closeBtn.disabled = true;

    // Create step elements
    steps.forEach((step, index) => {
        const stepElement = document.createElement('li');
        stepElement.className = 'progress-step pending';
        stepElement.id = `step-${index}`;
        stepElement.innerHTML = `
            <div class="step-icon" id="step-icon-${index}">
                <span class="status-icon">⏳</span>
            </div>
            <div class="step-content">
                <div class="step-title">${step.title}</div>
                <div class="step-description">${step.description}</div>
            </div>
        `;
        stepsContainer.appendChild(stepElement);
    });

    // Show modal
    modal.classList.add('active');

    // Setup close button
    closeBtn.onclick = () => {
        modal.classList.remove('active');
    };
}

function updateStepStatus(stepIndex, status, icon = null) {
    const stepElement = document.getElementById(`step-${stepIndex}`);
    const iconElement = document.getElementById(`step-icon-${stepIndex}`);

    if (!stepElement || !iconElement) return;

    // Remove all status classes
    stepElement.classList.remove('pending', 'in-progress', 'success', 'error', 'skipped');
    stepElement.classList.add(status);

    // Update icon
    const icons = {
        'pending': '⏳',
        'in-progress': '<div class="spinner"></div>',
        'success': '✅',
        'error': '❌',
        'skipped': '⚠️'
    };

    iconElement.innerHTML = icon || icons[status] || icons['pending'];
}

function enableModalClose() {
    const closeBtn = document.getElementById('closeModal');
    closeBtn.disabled = false;
}

// Setup form submission handler
function setupFormHandler() {
    const form = document.getElementById('dnsProxyForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating...';

        const resultDiv = document.getElementById('createResult');
        resultDiv.style.display = 'none';

        // Prepare form data
        const formData = new FormData(form);

        const data = {
            subdomain: formData.get('subdomain'),
            create_dns: formData.get('createDNS') === 'on',
            cname_target: formData.get('cnameTarget') || '@',
            ttl: parseInt(formData.get('ttl')) || 3600,
            target_host: formData.get('targetHost'),
            target_port: parseInt(formData.get('targetPort')),
            enable_ssl: formData.get('enableSSL') === 'on'
        };

        // Prepare steps based on configuration
        const steps = [];

        if (data.create_dns) {
            steps.push({
                title: 'Creating DNS CNAME Record',
                description: `Creating ${data.subdomain} → ${data.cname_target === '@' ? 'root domain' : data.cname_target}`
            });
        }

        steps.push({
            title: 'Creating NPM Proxy Host',
            description: `Configuring reverse proxy to ${data.target_host}:${data.target_port}`
        });

        if (data.enable_ssl) {
            steps.push({
                title: 'Configuring SSL Certificate',
                description: 'Setting up Let\'s Encrypt SSL certificate'
            });
        }

        // Show progress modal
        showProgressModal(steps);

        // Simulate progress with delays
        let currentStep = 0;
        const progressInterval = setInterval(() => {
            if (currentStep < steps.length) {
                updateStepStatus(currentStep, 'in-progress');
                currentStep++;
            }
        }, 600);

        try {
            const response = await fetch(`${API_URL}/api/dns-proxy`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            // Clear progress interval
            clearInterval(progressInterval);

            if (response.ok) {
                // Update steps based on result
                let stepIndex = 0;

                // DNS step
                if (data.create_dns) {
                    const dnsSuccess = result.dns_record_id !== null;
                    const dnsError = result.errors && result.errors.some(e => e.includes('DNS'));
                    updateStepStatus(stepIndex, dnsSuccess ? 'success' : (dnsError ? 'error' : 'success'));
                    stepIndex++;
                }

                // NPM step
                const npmSuccess = result.npm_proxy_host_id !== null;
                const npmError = result.errors && result.errors.some(e => e.includes('NPM'));
                updateStepStatus(stepIndex, npmSuccess ? 'success' : (npmError ? 'error' : 'success'));
                stepIndex++;

                // SSL step (if applicable)
                if (data.enable_ssl && stepIndex < steps.length) {
                    updateStepStatus(stepIndex, npmSuccess ? 'success' : 'error');
                }

                showResult(
                    result.success ? 'success' : 'warning',
                    result.message,
                    result.errors
                );

                if (result.success) {
                    form.reset();
                    // Reset all input validations
                    document.querySelectorAll('.input-feedback').forEach(el => {
                        el.className = 'input-feedback';
                        el.textContent = '';
                    });
                    document.querySelectorAll('input[type="text"], input[type="number"]').forEach(input => {
                        input.classList.remove('valid', 'invalid');
                    });
                    // Invalidate cache
                    cacheTimestamp = 0;
                    // Reload lists after a short delay
                    setTimeout(() => {
                        loadNPMHosts();
                        loadDNSRecords();
                    }, 1000);
                }
            } else {
                // Mark all remaining steps as error
                for (let i = 0; i < steps.length; i++) {
                    updateStepStatus(i, 'error');
                }
                showResult('error', result.detail || 'Failed to create DNS + NPM Host');
            }

        } catch (error) {
            clearInterval(progressInterval);
            console.error('Error creating DNS + NPM:', error);

            // Mark all steps as error
            for (let i = 0; i < steps.length; i++) {
                updateStepStatus(i, 'error');
            }

            showResult('error', 'Network error: ' + error.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create DNS + NPM Host';
            enableModalClose();
        }
    });
}

function showResult(type, message, errors = null) {
    const resultDiv = document.getElementById('createResult');
    resultDiv.className = `result-message ${type}`;

    let html = `<strong>${message}</strong>`;

    if (errors && errors.length > 0) {
        html += '<ul class="errors-list">';
        errors.forEach(error => {
            html += `<li>${error}</li>`;
        });
        html += '</ul>';
    }

    resultDiv.innerHTML = html;
    resultDiv.style.display = 'block';
}

// Filter NPM hosts based on search query
function filterNPMHosts(query) {
    const hostsContainer = document.getElementById('npmHostsList');
    const serviceCards = hostsContainer.querySelectorAll('.service-card');

    let visibleCount = 0;

    serviceCards.forEach(card => {
        const serviceName = card.querySelector('.service-name')?.textContent.toLowerCase() || '';
        const forwardTo = card.querySelector('.service-detail:nth-child(2) .detail-value')?.textContent.toLowerCase() || '';

        if (serviceName.includes(query) || forwardTo.includes(query)) {
            card.style.display = 'block';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });

    // Show message if no results
    const existingNoResults = hostsContainer.querySelector('.no-results');
    if (existingNoResults) {
        existingNoResults.remove();
    }

    if (visibleCount === 0 && serviceCards.length > 0 && query !== '') {
        const noResults = document.createElement('p');
        noResults.className = 'no-results empty-state';
        noResults.textContent = `No hosts found matching "${query}"`;
        hostsContainer.appendChild(noResults);
    }
}

// Filter DNS records based on search query
function filterDNSRecords(query) {
    const dnsContainer = document.getElementById('dnsRecordsList');
    const table = dnsContainer.querySelector('.dns-table');

    if (!table) return;

    const rows = table.querySelectorAll('tbody tr');
    let visibleCount = 0;

    rows.forEach(row => {
        const type = row.querySelector('.dns-type-badge')?.textContent.toLowerCase() || '';
        const subdomain = row.querySelector('.dns-subdomain')?.textContent.toLowerCase() || '';
        const target = row.querySelector('.dns-target')?.textContent.toLowerCase() || '';
        const ttl = row.cells[3]?.textContent.toLowerCase() || '';

        if (type.includes(query) || subdomain.includes(query) || target.includes(query) || ttl.includes(query)) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });

    // Show message if no results
    const existingNoResults = dnsContainer.querySelector('.no-results');
    if (existingNoResults) {
        existingNoResults.remove();
    }

    if (visibleCount === 0 && rows.length > 0 && query !== '') {
        const noResults = document.createElement('p');
        noResults.className = 'no-results empty-state';
        noResults.textContent = `No records found matching "${query}"`;
        dnsContainer.appendChild(noResults);
    }
}

// Load and display DNS records
async function loadDNSRecords() {
    const dnsContainer = document.getElementById('dnsRecordsList');

    try {
        const response = await fetch(`${API_URL}/api/dns/records`);
        const data = await response.json();

        if (!data.success || data.records.length === 0) {
            dnsContainer.innerHTML = '<p class="empty-state">No DNS records found or OVH API not accessible</p>';
            return;
        }

        // Update cache with fresh data
        if (data.success) {
            cachedDNSRecords = data.records;
            cacheTimestamp = Date.now();
        }

        // Create table
        let html = `
            <div style="margin-bottom: 15px;">
                <strong>Zone:</strong> ${data.zone} |
                <strong>Total records:</strong> ${data.count}
            </div>
            <table class="dns-table">
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Subdomain</th>
                        <th>Target</th>
                        <th>TTL</th>
                        <th style="text-align: right;">Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;

        // Sort records by type and subdomain
        data.records.sort((a, b) => {
            if (a.type !== b.type) return a.type.localeCompare(b.type);
            return a.subdomain.localeCompare(b.subdomain);
        });

        data.records.forEach(record => {
            const typeClass = `type-${record.type.toLowerCase()}`;
            const subdomain = record.subdomain === '@' ? `@ (${data.zone})` : `${record.subdomain}.${data.zone}`;
            const displayName = record.subdomain === '@' ? '@' : record.subdomain;
            // Escape quotes for onclick attribute
            const escapedName = displayName.replace(/'/g, "\\'");

            html += `
                <tr>
                    <td><span class="dns-type-badge ${typeClass}">${record.type}</span></td>
                    <td><span class="dns-subdomain">${subdomain}</span></td>
                    <td><span class="dns-target">${record.target}</span></td>
                    <td>${record.ttl || 'N/A'}</td>
                    <td>
                        <div class="dns-table-actions">
                            <button class="btn-delete-small" onclick="showDeleteModal('dns', ${record.id}, '${escapedName}')">
                                Delete
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        });

        html += `
                </tbody>
            </table>
        `;

        dnsContainer.innerHTML = html;

    } catch (error) {
        console.error('Failed to load DNS records:', error);
        dnsContainer.innerHTML = '<p class="error">Failed to load DNS records. Make sure OVH API is configured correctly.</p>';
    }
}

// Setup admin settings modal
function setupAdminModal() {
    const adminBtn = document.getElementById('adminBtn');
    const adminModal = document.getElementById('adminModal');

    // Tab management
    const tabs = document.querySelectorAll('.admin-tab');
    const tabContents = document.querySelectorAll('.admin-tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;

            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Update active content
            tabContents.forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`admin${tabName.charAt(0).toUpperCase() + tabName.slice(1)}Form`).classList.add('active');
        });
    });

    // Open admin modal
    if (adminBtn) {
        adminBtn.addEventListener('click', async () => {
            await loadAdminConfigs();
            adminModal.classList.add('active');
        });
    }

    // Close modal on overlay click
    if (adminModal) {
        adminModal.addEventListener('click', (e) => {
            if (e.target === adminModal) {
                adminModal.classList.remove('active');
            }
        });
    }

    // Setup NPM form
    setupNpmAdminForm();

    // Setup DNS form
    setupDnsAdminForm();
}

async function loadAdminConfigs() {
    // Load NPM config
    try {
        const response = await fetch(`${API_URL}/api/admin/npm-config`);
        if (response.ok) {
            const config = await response.json();
            document.getElementById('adminNpmUrl').value = config.npm_url;
            document.getElementById('adminNpmEmail').value = config.npm_email;
            document.getElementById('adminNpmPassword').value = '';
            document.getElementById('adminNpmPassword').placeholder = config.npm_password_masked;
        }
    } catch (error) {
        console.error('Error loading NPM config:', error);
    }

    // Load DNS config
    try {
        const response = await fetch(`${API_URL}/api/admin/dns-config`);
        if (response.ok) {
            const config = await response.json();

            // Set provider
            document.getElementById('dnsProvider').value = config.dns_provider;

            // OVH fields
            document.getElementById('ovhEndpoint').value = config.ovh_endpoint;
            document.getElementById('ovhAppKey').value = config.ovh_application_key || '';
            document.getElementById('ovhAppKey').placeholder = config.ovh_application_key_masked || 'Enter application key';
            document.getElementById('ovhAppSecret').value = '';
            document.getElementById('ovhAppSecret').placeholder = config.ovh_application_secret_masked || 'Enter application secret';
            document.getElementById('ovhConsumerKey').value = '';
            document.getElementById('ovhConsumerKey').placeholder = config.ovh_consumer_key_masked || 'Enter consumer key';
            document.getElementById('ovhZoneName').value = config.ovh_zone_name || '';

            // Cloudflare fields
            document.getElementById('cloudflareToken').value = '';
            document.getElementById('cloudflareToken').placeholder = config.cloudflare_api_token_masked || 'Enter API token';
            document.getElementById('cloudflareZoneId').value = config.cloudflare_zone_id || '';

            // Toggle sections
            toggleDnsProviderSections(config.dns_provider);

            // Trigger OVH credentials link update
            const ovhZoneNameInput = document.getElementById('ovhZoneName');
            if (ovhZoneNameInput) {
                ovhZoneNameInput.dispatchEvent(new Event('input'));
            }
        }
    } catch (error) {
        console.error('Error loading DNS config:', error);
    }
}

function setupNpmAdminForm() {
    const adminNpmForm = document.getElementById('adminNpmForm');
    const adminNpmCancelBtn = document.getElementById('adminNpmCancelBtn');
    const adminNpmSaveBtn = document.getElementById('adminNpmSaveBtn');
    const adminNpmFeedback = document.getElementById('adminNpmFeedback');
    const showNpmPassword = document.getElementById('showNpmPassword');
    const adminNpmPassword = document.getElementById('adminNpmPassword');
    const adminModal = document.getElementById('adminModal');

    // Toggle password visibility
    if (showNpmPassword && adminNpmPassword) {
        showNpmPassword.addEventListener('change', () => {
            adminNpmPassword.type = showNpmPassword.checked ? 'text' : 'password';
        });
    }

    // Cancel button
    if (adminNpmCancelBtn) {
        adminNpmCancelBtn.addEventListener('click', () => {
            adminModal.classList.remove('active');
        });
    }

    // Form submission
    if (adminNpmForm) {
        adminNpmForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            adminNpmSaveBtn.disabled = true;
            adminNpmSaveBtn.textContent = 'Saving...';
            adminNpmFeedback.style.display = 'none';

            try {
                const data = {
                    npm_url: document.getElementById('adminNpmUrl').value.trim(),
                    npm_email: document.getElementById('adminNpmEmail').value.trim(),
                    npm_password: document.getElementById('adminNpmPassword').value || null
                };

                const response = await fetch(`${API_URL}/api/admin/npm-config`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (response.ok && result.success) {
                    adminNpmFeedback.className = 'admin-feedback success';
                    adminNpmFeedback.textContent = result.message;
                    adminNpmFeedback.style.display = 'block';

                    setTimeout(() => {
                        adminModal.classList.remove('active');
                        checkHealth();
                    }, 1500);
                } else {
                    adminNpmFeedback.className = 'admin-feedback error';
                    adminNpmFeedback.textContent = result.message || 'Failed to update NPM configuration';
                    adminNpmFeedback.style.display = 'block';
                }
            } catch (error) {
                adminNpmFeedback.className = 'admin-feedback error';
                adminNpmFeedback.textContent = 'Network error: ' + error.message;
                adminNpmFeedback.style.display = 'block';
            } finally {
                adminNpmSaveBtn.disabled = false;
                adminNpmSaveBtn.textContent = 'Save NPM Config';
            }
        });
    }
}

function setupDnsAdminForm() {
    const adminDnsForm = document.getElementById('adminDnsForm');
    const adminDnsCancelBtn = document.getElementById('adminDnsCancelBtn');
    const adminDnsSaveBtn = document.getElementById('adminDnsSaveBtn');
    const adminDnsFeedback = document.getElementById('adminDnsFeedback');
    const dnsProvider = document.getElementById('dnsProvider');
    const adminModal = document.getElementById('adminModal');

    // Provider change handler
    if (dnsProvider) {
        dnsProvider.addEventListener('change', () => {
            toggleDnsProviderSections(dnsProvider.value);
        });
    }

    // Password toggles
    setupPasswordToggle('showOvhSecret', 'ovhAppSecret');
    setupPasswordToggle('showOvhConsumer', 'ovhConsumerKey');
    setupPasswordToggle('showCloudflareToken', 'cloudflareToken');

    // OVH Zone Name input listener - Generate dynamic credentials link
    const ovhZoneNameInput = document.getElementById('ovhZoneName');
    const ovhEndpointSelect = document.getElementById('ovhEndpoint');
    if (ovhZoneNameInput) {
        const updateOvhCredentialsLink = () => {
            const zoneName = ovhZoneNameInput.value.trim();
            const endpoint = ovhEndpointSelect ? ovhEndpointSelect.value : 'ovh-eu';

            if (zoneName) {
                // Show all steps
                document.getElementById('ovhStep2').style.display = 'list-item';
                document.getElementById('ovhStep3').style.display = 'list-item';
                document.getElementById('ovhStep4').style.display = 'list-item';
                document.getElementById('ovhStep5').style.display = 'list-item';
                document.getElementById('ovhStep6').style.display = 'list-item';
                document.getElementById('ovhNoZone').style.display = 'none';

                // Generate OVH credentials link with pre-filled permissions
                const rights = [
                    `GET /domain/zone/${zoneName}/*`,
                    `POST /domain/zone/${zoneName}/*`,
                    `DELETE /domain/zone/${zoneName}/*`
                ];

                const ovhLink = document.getElementById('ovhCredentialsLink');
                const baseUrl = 'https://api.ovh.com/createToken/';
                const params = new URLSearchParams();
                params.append('GET', `/domain/zone/${zoneName}/*`);
                params.append('POST', `/domain/zone/${zoneName}/*`);
                params.append('DELETE', `/domain/zone/${zoneName}/*`);

                ovhLink.href = `${baseUrl}?${params.toString()}`;
                ovhLink.textContent = `Generate OVH API Token for ${zoneName} →`;
            } else {
                // Hide steps if no zone name
                document.getElementById('ovhStep2').style.display = 'none';
                document.getElementById('ovhStep3').style.display = 'none';
                document.getElementById('ovhStep4').style.display = 'none';
                document.getElementById('ovhStep5').style.display = 'none';
                document.getElementById('ovhStep6').style.display = 'none';
                document.getElementById('ovhNoZone').style.display = 'block';
            }
        };

        ovhZoneNameInput.addEventListener('input', updateOvhCredentialsLink);
        if (ovhEndpointSelect) {
            ovhEndpointSelect.addEventListener('change', updateOvhCredentialsLink);
        }

        // Initial update on page load
        updateOvhCredentialsLink();
    }

    // Cancel button
    if (adminDnsCancelBtn) {
        adminDnsCancelBtn.addEventListener('click', () => {
            adminModal.classList.remove('active');
        });
    }

    // Form submission
    if (adminDnsForm) {
        adminDnsForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            adminDnsSaveBtn.disabled = true;
            adminDnsSaveBtn.textContent = 'Saving...';
            adminDnsFeedback.style.display = 'none';

            try {
                const provider = document.getElementById('dnsProvider').value;
                const data = {
                    dns_provider: provider
                };

                if (provider === 'ovh') {
                    data.ovh_endpoint = document.getElementById('ovhEndpoint').value;
                    data.ovh_application_key = document.getElementById('ovhAppKey').value || null;
                    data.ovh_application_secret = document.getElementById('ovhAppSecret').value || null;
                    data.ovh_consumer_key = document.getElementById('ovhConsumerKey').value || null;
                    data.ovh_zone_name = document.getElementById('ovhZoneName').value || null;
                } else {
                    data.cloudflare_api_token = document.getElementById('cloudflareToken').value || null;
                    data.cloudflare_zone_id = document.getElementById('cloudflareZoneId').value || null;
                }

                const response = await fetch(`${API_URL}/api/admin/dns-config`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (response.ok && result.success) {
                    adminDnsFeedback.className = 'admin-feedback success';
                    adminDnsFeedback.textContent = result.message;
                    adminDnsFeedback.style.display = 'block';

                    setTimeout(() => {
                        adminModal.classList.remove('active');
                        checkHealth(); // Reload health check and DNS provider label
                    }, 1500);
                } else {
                    adminDnsFeedback.className = 'admin-feedback error';
                    adminDnsFeedback.textContent = result.message || 'Failed to update DNS configuration';
                    adminDnsFeedback.style.display = 'block';
                }
            } catch (error) {
                adminDnsFeedback.className = 'admin-feedback error';
                adminDnsFeedback.textContent = 'Network error: ' + error.message;
                adminDnsFeedback.style.display = 'block';
            } finally {
                adminDnsSaveBtn.disabled = false;
                adminDnsSaveBtn.textContent = 'Save DNS Config';
            }
        });
    }
}

function toggleDnsProviderSections(provider) {
    const ovhSection = document.getElementById('ovhSection');
    const cloudflareSection = document.getElementById('cloudflareSection');

    if (provider === 'cloudflare') {
        ovhSection.style.display = 'none';
        cloudflareSection.style.display = 'block';
    } else {
        ovhSection.style.display = 'block';
        cloudflareSection.style.display = 'none';
    }
}

function setupPasswordToggle(checkboxId, inputId) {
    const checkbox = document.getElementById(checkboxId);
    const input = document.getElementById(inputId);

    if (checkbox && input) {
        checkbox.addEventListener('change', () => {
            input.type = checkbox.checked ? 'text' : 'password';
        });
    }
}
