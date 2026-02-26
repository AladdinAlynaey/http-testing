/**
 * HTTP Playground — Internationalization (i18n)
 * Supports English (en) and Arabic (ar) with automatic RTL
 */

const translations = {
    en: {
        // Header / Nav
        'nav.home': 'Home',
        'nav.docs': 'Docs',
        'nav.login': 'Login',
        'nav.register': 'Register',
        'nav.admin': 'Admin',
        'nav.logout': 'Logout',
        'nav.lang': 'عربي',

        // Hero
        'hero.title': 'Master HTTP & REST APIs',
        'hero.subtitle': 'A production-grade playground to learn HTTP requests, REST APIs, CURL commands, authentication, and API security — with real endpoints you can test right now.',
        'hero.badge.beginner': '15 Beginner Scenarios',
        'hero.badge.intermediate': '10 Intermediate Scenarios',
        'hero.badge.advanced': '5 Advanced + AI Scenarios',

        // Toolbar
        'toolbar.title': 'API Modules',
        'toolbar.count': '10 modules',
        'toolbar.all': 'All Levels',
        'toolbar.beginner': 'Beginner',
        'toolbar.intermediate': 'Intermediate',
        'toolbar.advanced': 'Advanced',

        // Quick Start
        'quickstart.title': '⚡ Quick Start',
        'quickstart.subtitle': 'Try these CURL commands right now — no authentication needed',

        // Login
        'login.title': 'Welcome Back',
        'login.subtitle': 'Login to access advanced endpoints & AI features',
        'login.username': 'Username',
        'login.username.placeholder': 'Enter your username',
        'login.password': 'Password',
        'login.password.placeholder': 'Enter your password',
        'login.btn': 'Login',
        'login.no_account': "Don't have an account?",
        'login.register_link': 'Register here',
        'login.success': 'Login successful! Redirecting...',
        'login.failed': 'Login failed. Please try again.',

        // Register
        'register.title': 'Create Account',
        'register.subtitle': 'Register to get your API key & access advanced features',
        'register.username': 'Username',
        'register.username.placeholder': 'Choose a username (3-30 chars)',
        'register.email': 'Email',
        'register.email.placeholder': 'your@email.com',
        'register.password': 'Password',
        'register.password.placeholder': 'Minimum 8 characters',
        'register.btn': 'Register',
        'register.has_account': 'Already have an account?',
        'register.login_link': 'Login here',
        'register.success': 'Registration successful!',
        'register.pending': 'Your account is pending admin approval. Once approved, you\'ll receive an API key.',
        'register.go_login': 'Go to Login →',
        'register.failed': 'Registration failed. Please try again.',

        // Admin
        'admin.title': 'Admin Dashboard',
        'admin.subtitle': 'Manage users, API keys, and monitor platform activity',
        'admin.tab.users': 'Users',
        'admin.tab.keys': 'API Keys',
        'admin.tab.audit': 'Audit Log',
        'admin.filter.all': 'All Users',
        'admin.filter.pending': 'Pending',
        'admin.filter.approved': 'Approved',
        'admin.filter.rejected': 'Rejected',
        'admin.stat.total': 'Total Users',
        'admin.stat.pending': 'Pending Approval',
        'admin.stat.keys': 'Active API Keys',
        'admin.stat.logs': 'Logs (24h)',
        'admin.table.id': 'ID',
        'admin.table.username': 'Username',
        'admin.table.email': 'Email',
        'admin.table.role': 'Role',
        'admin.table.status': 'Status',
        'admin.table.created': 'Created',
        'admin.table.actions': 'Actions',
        'admin.table.user': 'User',
        'admin.table.key': 'Key',
        'admin.table.scope': 'Scope',
        'admin.table.active': 'Active',
        'admin.table.lastused': 'Last Used',
        'admin.table.userid': 'User ID',
        'admin.table.action': 'Action',
        'admin.table.resource': 'Resource',
        'admin.table.ip': 'IP',
        'admin.table.time': 'Time',
        'admin.denied': 'Access denied or session expired.',
        'admin.login_again': 'Login again',
        'admin.no_users': 'No users found',
        'admin.no_keys': 'No API keys',
        'admin.no_logs': 'No logs',
        'admin.revoke': 'Revoke',
        'admin.revoked': 'API key revoked',

        // Docs
        'docs.title': 'API Documentation',
        'docs.subtitle': 'Complete reference with CURL examples',

        // Footer
        'footer.built': 'Built by',
        'footer.powered': 'Powered by AI via',
        'footer.docs': 'Documentation',
        'footer.examples': 'CURL Examples',
        'footer.security': 'Security',

        // Module Cards
        'module.library': 'Library System',
        'module.library.desc': 'Manage a collection of books with full CRUD operations, search, and genre filtering.',
        'module.menu': 'Restaurant Menu',
        'module.menu.desc': 'Manage restaurant menu items with categories, prices, and availability status.',
        'module.tasks': 'Task Manager',
        'module.tasks.desc': 'Track tasks with status updates, priority levels, and assignment management.',
        'module.students': 'Student Management',
        'module.students.desc': 'Manage student records with enrollment data, GPA tracking, and major filtering.',
        'module.notes': 'Notes System',
        'module.notes.desc': 'Create and organize notes with categories and pinning functionality.',
        'module.files': 'File Manager',
        'module.files.desc': 'Upload and download files. Learn multipart form data handling.',
        'module.blog': 'Blog Platform',
        'module.blog.desc': 'Full blog system with posts, tags, and publishing workflow.',
        'module.inventory': 'Inventory System',
        'module.inventory.desc': 'Track inventory across warehouses with stock monitoring.',
        'module.weather': 'Mock Weather API',
        'module.weather.desc': 'Practice with weather data for 10 cities. Compare temperatures.',
        'module.ai': 'AI Assistant',
        'module.ai.desc': 'AI-powered text generation, summarization, classification, and chat.',

        // Common
        'copy': 'Copy',
        'copied': 'Copied!',
    },

    ar: {
        // Header / Nav
        'nav.home': 'الرئيسية',
        'nav.docs': 'التوثيق',
        'nav.login': 'تسجيل الدخول',
        'nav.register': 'إنشاء حساب',
        'nav.admin': 'لوحة التحكم',
        'nav.logout': 'تسجيل الخروج',
        'nav.lang': 'English',

        // Hero
        'hero.title': 'أتقن HTTP و REST APIs',
        'hero.subtitle': 'منصة تعليمية احترافية لتعلم طلبات HTTP، واجهات REST APIs، أوامر CURL، المصادقة، وأمان الـ API — مع نقاط نهاية حقيقية يمكنك اختبارها الآن.',
        'hero.badge.beginner': '15 سيناريو للمبتدئين',
        'hero.badge.intermediate': '10 سيناريوهات متوسطة',
        'hero.badge.advanced': '5 سيناريوهات متقدمة + ذكاء اصطناعي',

        // Toolbar
        'toolbar.title': 'وحدات API',
        'toolbar.count': '10 وحدات',
        'toolbar.all': 'جميع المستويات',
        'toolbar.beginner': 'مبتدئ',
        'toolbar.intermediate': 'متوسط',
        'toolbar.advanced': 'متقدم',

        // Quick Start
        'quickstart.title': '⚡ البدء السريع',
        'quickstart.subtitle': 'جرّب أوامر CURL هذه الآن — بدون مصادقة',

        // Login
        'login.title': 'مرحباً بعودتك',
        'login.subtitle': 'سجّل دخولك للوصول إلى النقاط المتقدمة وميزات الذكاء الاصطناعي',
        'login.username': 'اسم المستخدم',
        'login.username.placeholder': 'أدخل اسم المستخدم',
        'login.password': 'كلمة المرور',
        'login.password.placeholder': 'أدخل كلمة المرور',
        'login.btn': 'تسجيل الدخول',
        'login.no_account': 'ليس لديك حساب؟',
        'login.register_link': 'سجّل من هنا',
        'login.success': 'تم تسجيل الدخول بنجاح! جاري التحويل...',
        'login.failed': 'فشل تسجيل الدخول. حاول مرة أخرى.',

        // Register
        'register.title': 'إنشاء حساب',
        'register.subtitle': 'سجّل للحصول على مفتاح API والوصول للميزات المتقدمة',
        'register.username': 'اسم المستخدم',
        'register.username.placeholder': 'اختر اسم مستخدم (3-30 حرف)',
        'register.email': 'البريد الإلكتروني',
        'register.email.placeholder': 'your@email.com',
        'register.password': 'كلمة المرور',
        'register.password.placeholder': '8 أحرف كحد أدنى',
        'register.btn': 'إنشاء حساب',
        'register.has_account': 'لديك حساب بالفعل؟',
        'register.login_link': 'سجّل دخولك',
        'register.success': 'تم التسجيل بنجاح!',
        'register.pending': 'حسابك قيد الانتظار لموافقة المسؤول. بمجرد الموافقة، ستحصل على مفتاح API.',
        'register.go_login': 'انتقل لتسجيل الدخول ←',
        'register.failed': 'فشل التسجيل. حاول مرة أخرى.',

        // Admin
        'admin.title': 'لوحة التحكم',
        'admin.subtitle': 'إدارة المستخدمين ومفاتيح API ومراقبة نشاط المنصة',
        'admin.tab.users': 'المستخدمون',
        'admin.tab.keys': 'مفاتيح API',
        'admin.tab.audit': 'سجل المراجعة',
        'admin.filter.all': 'جميع المستخدمين',
        'admin.filter.pending': 'قيد الانتظار',
        'admin.filter.approved': 'مقبول',
        'admin.filter.rejected': 'مرفوض',
        'admin.stat.total': 'إجمالي المستخدمين',
        'admin.stat.pending': 'بانتظار الموافقة',
        'admin.stat.keys': 'مفاتيح API النشطة',
        'admin.stat.logs': 'السجلات (24 ساعة)',
        'admin.table.id': 'المعرّف',
        'admin.table.username': 'اسم المستخدم',
        'admin.table.email': 'البريد الإلكتروني',
        'admin.table.role': 'الدور',
        'admin.table.status': 'الحالة',
        'admin.table.created': 'تاريخ الإنشاء',
        'admin.table.actions': 'الإجراءات',
        'admin.table.user': 'المستخدم',
        'admin.table.key': 'المفتاح',
        'admin.table.scope': 'النطاق',
        'admin.table.active': 'نشط',
        'admin.table.lastused': 'آخر استخدام',
        'admin.table.userid': 'معرّف المستخدم',
        'admin.table.action': 'الإجراء',
        'admin.table.resource': 'المورد',
        'admin.table.ip': 'عنوان IP',
        'admin.table.time': 'الوقت',
        'admin.denied': 'تم رفض الوصول أو انتهت الجلسة.',
        'admin.login_again': 'سجّل دخولك مجدداً',
        'admin.no_users': 'لا يوجد مستخدمون',
        'admin.no_keys': 'لا توجد مفاتيح API',
        'admin.no_logs': 'لا توجد سجلات',
        'admin.revoke': 'إلغاء',
        'admin.revoked': 'تم إلغاء مفتاح API',

        // Docs
        'docs.title': 'توثيق API',
        'docs.subtitle': 'مرجع شامل مع أمثلة CURL',

        // Footer
        'footer.built': 'بُني بواسطة',
        'footer.powered': 'مدعوم بالذكاء الاصطناعي عبر',
        'footer.docs': 'التوثيق',
        'footer.examples': 'أمثلة CURL',
        'footer.security': 'الأمان',

        // Module Cards
        'module.library': 'نظام المكتبة',
        'module.library.desc': 'إدارة مجموعة الكتب مع عمليات CRUD الكاملة، البحث، وتصفية الأنواع.',
        'module.menu': 'قائمة المطعم',
        'module.menu.desc': 'إدارة عناصر قائمة المطعم مع الفئات والأسعار وحالة التوفر.',
        'module.tasks': 'مدير المهام',
        'module.tasks.desc': 'تتبع المهام مع تحديثات الحالة ومستويات الأولوية وإدارة التكليف.',
        'module.students': 'إدارة الطلاب',
        'module.students.desc': 'إدارة سجلات الطلاب مع بيانات التسجيل وتتبع المعدل وتصفية التخصصات.',
        'module.notes': 'نظام الملاحظات',
        'module.notes.desc': 'إنشاء وتنظيم الملاحظات مع الفئات وميزة التثبيت.',
        'module.files': 'مدير الملفات',
        'module.files.desc': 'رفع وتحميل الملفات. تعلم التعامل مع بيانات multipart.',
        'module.blog': 'منصة المدونة',
        'module.blog.desc': 'نظام مدونة كامل مع المنشورات والوسوم وسير عمل النشر.',
        'module.inventory': 'نظام المخزون',
        'module.inventory.desc': 'تتبع المخزون عبر المستودعات مع مراقبة المخزون.',
        'module.weather': 'واجهة الطقس',
        'module.weather.desc': 'تدرّب مع بيانات الطقس لـ 10 مدن. قارن درجات الحرارة.',
        'module.ai': 'مساعد الذكاء الاصطناعي',
        'module.ai.desc': 'توليد النصوص، التلخيص، التصنيف، والمحادثة بالذكاء الاصطناعي.',

        // Common
        'copy': 'نسخ',
        'copied': 'تم النسخ!',
    }
};

// ============================================================
// i18n Engine
// ============================================================
function getCurrentLang() {
    return localStorage.getItem('lang') || 'en';
}

function t(key) {
    const lang = getCurrentLang();
    return translations[lang]?.[key] || translations['en']?.[key] || key;
}

function setLanguage(lang) {
    localStorage.setItem('lang', lang);
    applyLanguage(lang);
}

function toggleLanguage() {
    const current = getCurrentLang();
    const next = current === 'en' ? 'ar' : 'en';
    setLanguage(next);
}

function applyLanguage(lang) {
    const html = document.documentElement;

    // Set direction and lang attribute
    if (lang === 'ar') {
        html.setAttribute('dir', 'rtl');
        html.setAttribute('lang', 'ar');
    } else {
        html.setAttribute('dir', 'ltr');
        html.setAttribute('lang', 'en');
    }

    // Update all elements with data-i18n attribute (text content)
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const val = t(key);
        if (val) el.textContent = val;
    });

    // Update all elements with data-i18n-placeholder (input placeholders)
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        const val = t(key);
        if (val) el.placeholder = val;
    });

    // Update all elements with data-i18n-html (innerHTML)
    document.querySelectorAll('[data-i18n-html]').forEach(el => {
        const key = el.getAttribute('data-i18n-html');
        const val = t(key);
        if (val) el.innerHTML = val;
    });

    // Update lang toggle button text
    const langBtn = document.getElementById('lang-toggle');
    if (langBtn) {
        langBtn.textContent = t('nav.lang');
    }
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    const lang = getCurrentLang();
    applyLanguage(lang);
});
