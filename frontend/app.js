// API Configuration
const API_URL = 'http://localhost:8000';

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    loadNPMHosts();
    loadDNSRecords();
    setupFormHandler();
    setupToggleButtons();

    // Refresh NPM hosts and DNS records every 30 seconds
    setInterval(() => {
        loadNPMHosts();
        loadDNSRecords();
    }, 30000);
});

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
    } catch (error) {
        console.error('Health check failed:', error);
        updateStatusIndicator('dockerStatus', false, 'Cannot reach API');
        updateStatusIndicator('npmStatus', false, 'Cannot reach API');
        updateStatusIndicator('ovhStatus', false, 'Cannot reach API');
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

    } catch (error) {
        console.error('Failed to load NPM hosts:', error);
        hostsContainer.innerHTML = '<p class="error">Failed to load NPM hosts</p>';
    }
}

function createNPMHostCard(host) {
    const domain = host.domain_names && host.domain_names.length > 0 ? host.domain_names[0] : 'N/A';
    const sslStatus = host.certificate_id ? 'SSL Enabled' : 'No SSL';
    const sslClass = host.certificate_id ? 'active' : 'partial';

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
        </div>
    `;
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

        try {
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

            const response = await fetch(`${API_URL}/api/dns-proxy`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) {
                showResult(
                    result.success ? 'success' : 'warning',
                    result.message,
                    result.errors
                );

                if (result.success) {
                    form.reset();
                    loadNPMHosts();
                    loadDNSRecords();
                }
            } else {
                showResult('error', result.detail || 'Failed to create DNS + NPM Host');
            }

        } catch (error) {
            console.error('Error creating DNS + NPM:', error);
            showResult('error', 'Network error: ' + error.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create DNS + NPM Host';
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

            html += `
                <tr>
                    <td><span class="dns-type-badge ${typeClass}">${record.type}</span></td>
                    <td><span class="dns-subdomain">${subdomain}</span></td>
                    <td><span class="dns-target">${record.target}</span></td>
                    <td>${record.ttl || 'N/A'}</td>
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
