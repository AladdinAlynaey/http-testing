/**
 * HTTP Playground v3.0 — Main JavaScript
 * 20 module cards, theme toggle, auth state, dual API key display
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

// ============ MODULES DATA (20 MODULES) ============
const MODULES = [
    { name: 'Library System', slug: 'books', icon: '📚', desc: 'Full CRUD on books. Search by genre, author, title. 15 seed books with filtering and pagination.', level: 'beginner', auth: 'None', path: '/api/books', color: '#6366f1' },
    { name: 'Restaurant Menu', slug: 'menu', icon: '🍽️', desc: 'Create and manage restaurant menu items. Filter by category, update prices, availability control.', level: 'beginner', auth: 'None', path: '/api/menu', color: '#ec4899' },
    { name: 'Task Manager', slug: 'tasks', icon: '✅', desc: 'Organize tasks with priorities, status tracking, due dates, and assignees. Filter by status/priority.', level: 'beginner', auth: 'None', path: '/api/tasks', color: '#10b981' },
    { name: 'Student Records', slug: 'students', icon: '🎓', desc: 'Student records with GPA, major, enrollment year. API key needed for PUT/DELETE.', level: 'intermediate', auth: 'API Key', path: '/api/students', color: '#f59e0b' },
    { name: 'Notes System', slug: 'notes', icon: '📝', desc: 'Create, categorize, and pin notes. Filter by category, search content.', level: 'beginner', auth: 'None', path: '/api/notes', color: '#8b5cf6' },
    { name: 'File Manager', slug: 'files', icon: '📁', desc: 'Upload & download files securely. Extension whitelist + magic byte validation + 2MB limit.', level: 'intermediate', auth: 'API Key', path: '/api/files', color: '#06b6d4' },
    { name: 'Blog Platform', slug: 'blog', icon: '✍️', desc: 'Full blog with posts, tags, publishing control. Public read, API key for writing.', level: 'beginner', auth: 'None / Key', path: '/api/blog', color: '#f97316' },
    { name: 'Inventory System', slug: 'inventory', icon: '📦', desc: 'Track stock, SKUs, warehouses, pricing. Low-stock API for monitoring.', level: 'intermediate', auth: 'API Key', path: '/api/inventory', color: '#14b8a6' },
    { name: 'Product Store', slug: 'products', icon: '🛍️', desc: 'E-commerce products with brands, ratings, stock. Top-rated endpoint included.', level: 'beginner', auth: 'None', path: '/api/products', color: '#a855f7' },
    { name: 'Movie Database', slug: 'movies', icon: '🎬', desc: 'Movies with directors, genres, ratings, runtimes. Top-rated + language filters.', level: 'beginner', auth: 'None', path: '/api/movies', color: '#e11d48' },
    { name: 'Recipe Book', slug: 'recipes', icon: '🧑‍🍳', desc: 'Cooking recipes with ingredients, cuisine, difficulty, prep & cook times.', level: 'beginner', auth: 'None', path: '/api/recipes', color: '#ea580c' },
    { name: 'Event Calendar', slug: 'events', icon: '📅', desc: 'Calendar events with dates, locations, capacity. Upcoming events endpoint.', level: 'beginner', auth: 'None', path: '/api/events', color: '#0284c7' },
    { name: 'Address Book', slug: 'contacts', icon: '📇', desc: 'Contact management with company, job title, location. Search by company/country.', level: 'intermediate', auth: 'API Key', path: '/api/contacts', color: '#16a34a' },
    { name: 'Music Library', slug: 'songs', icon: '🎵', desc: 'Songs with artists, albums, genres, durations. Filter by genre, year, explicit.', level: 'beginner', auth: 'None', path: '/api/songs', color: '#7c3aed' },
    { name: 'Quotes Collection', slug: 'quotes', icon: '💬', desc: 'Inspirational quotes from famous people. Random quote endpoint included.', level: 'beginner', auth: 'None', path: '/api/quotes', color: '#0891b2' },
    { name: 'World Countries', slug: 'countries', icon: '🌍', desc: 'Country data: capitals, populations, currencies, continents. By-continent grouping.', level: 'beginner', auth: 'None', path: '/api/countries', color: '#059669' },
    { name: 'Joke API', slug: 'jokes', icon: '😂', desc: 'Programming jokes with setup/punchline. Random joke endpoint for quick laughs.', level: 'beginner', auth: 'None', path: '/api/jokes', color: '#d946ef' },
    { name: 'Vehicle Market', slug: 'vehicles', icon: '🚗', desc: 'Cars & trucks with make, model, year, fuel type. Filter by type, color, fuel.', level: 'intermediate', auth: 'API Key', path: '/api/vehicles', color: '#dc2626' },
    { name: 'Online Courses', slug: 'courses', icon: '🎓', desc: 'Course catalog with instructors, ratings, enrollment. Free courses + popular endpoints.', level: 'beginner', auth: 'None', path: '/api/courses', color: '#2563eb' },
    { name: 'Pet Adoption', slug: 'pets', icon: '🐾', desc: 'Pet adoption: dogs, cats with breeds, ages, shelters. Available-for-adoption filter.', level: 'beginner', auth: 'None', path: '/api/pets', color: '#ca8a04' },
    { name: 'Weather API', slug: 'weather', icon: '🌤️', desc: 'Mock weather for 12 cities. Compare temperatures, 5-day forecasts. Read-only.', level: 'beginner', auth: 'None', path: '/api/weather', color: '#3b82f6' },
    { name: 'AI Assistant', slug: 'ai', icon: '🤖', desc: 'AI text generation, summarization, chat, classification via OpenRouter. Requires AI API key.', level: 'advanced', auth: 'AI Key', path: '/api/ai/*', color: '#ef4444' },
];

// ============ RENDER CARDS ============
function renderModuleCards(filter = 'all') {
    const grid = document.getElementById('modules-grid');
    if (!grid) return;

    const filtered = filter === 'all' ? MODULES : MODULES.filter(m => m.level === filter);
    grid.innerHTML = filtered.map(m => {
        const isFeatured = m.slug === 'ai';
        return `
        <div class="card${isFeatured ? ' card-featured' : ''}" onclick="window.location.href='/module/${m.slug}'" style="--card-accent:${m.color};border:1px solid ${m.color}22">
            <div class="card-image-placeholder" style="background:linear-gradient(135deg, ${m.color}20, ${m.color}08)">
                <span>${m.icon}</span>
            </div>
            <div class="card-body">
                <div class="card-title">${m.name}</div>
                <div class="card-desc">${m.desc}</div>
                <div class="card-meta">
                    <span class="card-badge ${m.level}">${m.level.toUpperCase()}</span>
                    <span class="card-badge auth-${m.auth === 'None' ? 'none' : m.auth === 'AI Key' ? 'ai' : m.auth === 'API Key' ? 'key' : 'mixed'}">
                        ${m.auth === 'None' ? '🔓 Public' : m.auth === 'API Key' ? '🔑 API Key' : m.auth === 'AI Key' ? '🤖 AI Key' : '🔓/🔑'}
                    </span>
                    <span class="card-badge" style="background:var(--bg-glass);color:var(--text-secondary);font-family:'JetBrains Mono',monospace;font-size:.75rem">
                        ${m.path}
                    </span>
                </div>
            </div>
        </div>
    `}).join('');

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
