/**
 * HTTP Playground - Main JavaScript
 * Theme toggle, navigation, card rendering, API interactions
 */

const API_BASE = '';
let currentUser = null;
let currentView = 'grid';

// ============ THEME ============
function initTheme() {
    const saved = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
    updateThemeIcon(saved);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    updateThemeIcon(next);
}

function updateThemeIcon(theme) {
    const btns = document.querySelectorAll('.theme-toggle');
    btns.forEach(b => b.textContent = theme === 'dark' ? '☀️' : '🌙');
}

// ============ AUTH STATE ============
function checkAuth() {
    const token = localStorage.getItem('access_token');
    const userData = localStorage.getItem('user_data');
    if (token && userData) {
        try {
            currentUser = JSON.parse(userData);
            updateNavForUser();
        } catch (e) {
            logout();
        }
    }
}

function updateNavForUser() {
    const authNav = document.getElementById('auth-nav');
    if (!authNav) return;
    if (currentUser) {
        let adminLink = '';
        if (['admin', 'superadmin'].includes(currentUser.role)) {
            adminLink = '<a href="/admin"><i class="fas fa-shield-alt"></i> <span>Admin</span></a>';
        }
        authNav.innerHTML = `
            ${adminLink}
            <span style="color:var(--text-secondary);font-size:0.85rem">
                <i class="fas fa-user"></i> ${currentUser.username}
            </span>
            <button onclick="logout()" class="btn-sm" style="color:var(--danger)">
                <i class="fas fa-sign-out-alt"></i> <span>Logout</span>
            </button>
        `;
    } else {
        authNav.innerHTML = `
            <a href="/login"><i class="fas fa-sign-in-alt"></i> <span>Login</span></a>
            <a href="/register" class="btn-primary"><i class="fas fa-user-plus"></i> <span>Register</span></a>
        `;
    }
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_data');
    localStorage.removeItem('api_key');
    currentUser = null;
    window.location.href = '/';
}

// ============ API HELPERS ============
async function apiRequest(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const apiKey = localStorage.getItem('api_key');
    if (apiKey) headers['X-API-Key'] = apiKey;

    try {
        const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers });
        const data = await res.json();
        if (!res.ok) throw { status: res.status, ...data };
        return data;
    } catch (err) {
        if (err.status === 401) {
            const refreshed = await refreshAccessToken();
            if (refreshed) return apiRequest(endpoint, options);
        }
        throw err;
    }
}

async function refreshAccessToken() {
    const rt = localStorage.getItem('refresh_token');
    if (!rt) return false;
    try {
        const res = await fetch(`${API_BASE}/api/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: rt })
        });
        if (!res.ok) return false;
        const data = await res.json();
        localStorage.setItem('access_token', data.access_token);
        return true;
    } catch {
        return false;
    }
}

// ============ TOAST NOTIFICATIONS ============
function showToast(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3000);
}

// ============ MODULES DATA ============
const MODULES = [
    { name: 'Library System', slug: 'books', icon: '📚', desc: 'Manage books with full CRUD operations. Search by genre, author, or title. Perfect for learning REST basics.', level: 'beginner', auth: 'None', path: '/api/books', color: '#6366f1' },
    { name: 'Restaurant Menu', slug: 'menu', icon: '🍽️', desc: 'Create and manage restaurant menu items. Filter by category, update prices, and control availability.', level: 'beginner', auth: 'None', path: '/api/menu', color: '#ec4899' },
    { name: 'Task Manager', slug: 'tasks', icon: '✅', desc: 'Organize tasks with priorities and status tracking. Learn about filtering, sorting, and state management.', level: 'beginner', auth: 'None', path: '/api/tasks', color: '#10b981' },
    { name: 'Student Management', slug: 'students', icon: '🎓', desc: 'Manage student records with enrollment data and GPA tracking. Requires API key authentication.', level: 'intermediate', auth: 'API Key', path: '/api/students', color: '#f59e0b' },
    { name: 'Notes System', slug: 'notes', icon: '📝', desc: 'Create, pin, and categorize notes. Learn about CRUD operations with additional features like pinning.', level: 'beginner', auth: 'None', path: '/api/notes', color: '#8b5cf6' },
    { name: 'File Manager', slug: 'files', icon: '📁', desc: 'Upload and download files securely. Learn about multipart form data, file validation, and secure storage.', level: 'intermediate', auth: 'API Key', path: '/api/files', color: '#06b6d4' },
    { name: 'Blog Platform', slug: 'blog', icon: '✍️', desc: 'Full blog system with posts, tags, and publishing control. Public read, API key required for writing.', level: 'beginner', auth: 'None / API Key', path: '/api/blog', color: '#f97316' },
    { name: 'Inventory System', slug: 'inventory', icon: '📦', desc: 'Track inventory across warehouses. Monitor stock levels, manage SKUs, and filter by category.', level: 'intermediate', auth: 'API Key', path: '/api/inventory', color: '#14b8a6' },
    { name: 'Weather API', slug: 'weather', icon: '🌤️', desc: 'Mock weather data for 10 cities worldwide. Compare temperatures between cities. Great for API practice.', level: 'beginner', auth: 'None', path: '/api/weather', color: '#3b82f6' },
    { name: 'AI Assistant', slug: 'ai', icon: '🤖', desc: 'AI-powered text generation, summarization, classification, and validation using OpenRouter. Login required.', level: 'advanced', auth: 'Login', path: '/api/ai/*', color: '#ef4444' },
];

// ============ RENDER CARDS ============
function renderModuleCards(filter = 'all') {
    const grid = document.getElementById('modules-grid');
    if (!grid) return;

    const filtered = filter === 'all' ? MODULES : MODULES.filter(m => m.level === filter);
    grid.innerHTML = filtered.map(m => `
        <div class="card" onclick="window.location.href='/module/${m.slug}'">
            <div class="card-image-placeholder" style="background:linear-gradient(135deg, ${m.color}22, ${m.color}11)">
                <span>${m.icon}</span>
            </div>
            <div class="card-body">
                <div class="card-title">${m.name}</div>
                <div class="card-desc">${m.desc}</div>
                <div class="card-meta">
                    <span class="card-badge ${m.level}">${m.level}</span>
                    <span class="card-badge auth-${m.auth === 'None' ? 'none' : m.auth === 'API Key' ? 'key' : 'login'}">
                        ${m.auth === 'None' ? '🔓 Public' : m.auth === 'API Key' ? '🔑 API Key' : '🔐 Login'}
                    </span>
                    <span class="card-badge" style="background:var(--bg-glass);color:var(--text-secondary)">
                        ${m.path}
                    </span>
                </div>
            </div>
        </div>
    `).join('');

    const countEl = document.getElementById('modules-count');
    if (countEl) countEl.textContent = `${filtered.length} modules`;
}

function setView(view) {
    currentView = view;
    const grid = document.getElementById('modules-grid');
    if (!grid) return;
    grid.classList.toggle('list-view', view === 'list');
    document.querySelectorAll('.view-toggle button').forEach(b => {
        b.classList.toggle('active', b.dataset.view === view);
    });
}

// ============ COPY TO CLIPBOARD ============
function copyCode(btn) {
    const code = btn.parentElement.querySelector('code') || btn.parentElement;
    const text = code.textContent.replace('Copy', '').trim();
    navigator.clipboard.writeText(text).then(() => {
        btn.textContent = 'Copied!';
        setTimeout(() => btn.textContent = 'Copy', 2000);
    });
}

// ============ INIT ============
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    checkAuth();
    renderModuleCards();
});
