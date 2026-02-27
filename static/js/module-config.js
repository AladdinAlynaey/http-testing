/**
 * Module field definitions, table columns, and CURL templates for all 20 modules.
 * Separated from module.html to avoid Jinja/JS template literal conflicts.
 */

const BASE_URL = window.location.origin;

const MODULE_FIELDS = {
    books: [
        { name: 'title', label: 'Title', type: 'text', required: true },
        { name: 'author', label: 'Author', type: 'text', required: true },
        { name: 'isbn', label: 'ISBN', type: 'text' },
        { name: 'genre', label: 'Genre', type: 'select', options: ['Fiction', 'Technology', 'Science', 'History', 'Self-Help', 'Dystopian', 'Science Fiction', 'Philosophy', 'Business'] },
        { name: 'year', label: 'Year', type: 'number' },
        { name: 'available', label: 'Available', type: 'select', options: ['1', '0'] }
    ],
    menu: [
        { name: 'name', label: 'Name', type: 'text', required: true },
        { name: 'description', label: 'Description', type: 'textarea' },
        { name: 'price', label: 'Price', type: 'number', step: '0.01', required: true },
        { name: 'category', label: 'Category', type: 'select', options: ['Main Course', 'Appetizer', 'Dessert', 'Beverage', 'Sides'] },
        { name: 'is_available', label: 'Available', type: 'select', options: ['1', '0'] }
    ],
    tasks: [
        { name: 'title', label: 'Title', type: 'text', required: true },
        { name: 'description', label: 'Description', type: 'textarea' },
        { name: 'status', label: 'Status', type: 'select', options: ['pending', 'in_progress', 'completed'] },
        { name: 'priority', label: 'Priority', type: 'select', options: ['low', 'medium', 'high'] },
        { name: 'due_date', label: 'Due Date', type: 'date' },
        { name: 'assigned_to', label: 'Assigned To', type: 'text' }
    ],
    students: [
        { name: 'name', label: 'Name', type: 'text', required: true },
        { name: 'email', label: 'Email', type: 'email' },
        { name: 'student_id', label: 'Student ID', type: 'text' },
        { name: 'major', label: 'Major', type: 'text' },
        { name: 'gpa', label: 'GPA', type: 'number', step: '0.01' },
        { name: 'enrollment_year', label: 'Enrollment Year', type: 'number' }
    ],
    notes: [
        { name: 'title', label: 'Title', type: 'text', required: true },
        { name: 'content', label: 'Content', type: 'textarea' },
        { name: 'category', label: 'Category', type: 'select', options: ['Work', 'Personal', 'Learning', 'Ideas'] },
        { name: 'is_pinned', label: 'Pinned', type: 'select', options: ['0', '1'] }
    ],
    files: [],
    blog: [
        { name: 'title', label: 'Title', type: 'text', required: true },
        { name: 'content', label: 'Content', type: 'textarea', required: true },
        { name: 'author', label: 'Author', type: 'text' },
        { name: 'tags', label: 'Tags', type: 'text' },
        { name: 'is_published', label: 'Published', type: 'select', options: ['1', '0'] }
    ],
    inventory: [
        { name: 'name', label: 'Name', type: 'text', required: true },
        { name: 'sku', label: 'SKU', type: 'text' },
        { name: 'quantity', label: 'Quantity', type: 'number' },
        { name: 'price', label: 'Price', type: 'number', step: '0.01' },
        { name: 'category', label: 'Category', type: 'text' },
        { name: 'warehouse', label: 'Warehouse', type: 'text' }
    ],
    products: [
        { name: 'name', label: 'Name', type: 'text', required: true },
        { name: 'description', label: 'Description', type: 'textarea' },
        { name: 'price', label: 'Price', type: 'number', step: '0.01', required: true },
        { name: 'category', label: 'Category', type: 'text' },
        { name: 'brand', label: 'Brand', type: 'text' },
        { name: 'rating', label: 'Rating', type: 'number', step: '0.1' },
        { name: 'stock', label: 'Stock', type: 'number' }
    ],
    movies: [
        { name: 'title', label: 'Title', type: 'text', required: true },
        { name: 'director', label: 'Director', type: 'text' },
        { name: 'genre', label: 'Genre', type: 'select', options: ['Action', 'Comedy', 'Drama', 'Sci-Fi', 'Thriller', 'Animation', 'Crime', 'Horror'] },
        { name: 'year', label: 'Year', type: 'number' },
        { name: 'rating', label: 'Rating', type: 'number', step: '0.1' },
        { name: 'runtime', label: 'Runtime (min)', type: 'number' },
        { name: 'language', label: 'Language', type: 'text' }
    ],
    recipes: [
        { name: 'title', label: 'Title', type: 'text', required: true },
        { name: 'description', label: 'Description', type: 'textarea' },
        { name: 'cuisine', label: 'Cuisine', type: 'select', options: ['Italian', 'Asian', 'Mexican', 'Mediterranean', 'Thai', 'American', 'Indian', 'French'] },
        { name: 'difficulty', label: 'Difficulty', type: 'select', options: ['easy', 'medium', 'hard'] },
        { name: 'prep_time', label: 'Prep Time', type: 'number' },
        { name: 'cook_time', label: 'Cook Time', type: 'number' },
        { name: 'servings', label: 'Servings', type: 'number' },
        { name: 'ingredients', label: 'Ingredients', type: 'textarea' }
    ],
    events: [
        { name: 'title', label: 'Title', type: 'text', required: true },
        { name: 'description', label: 'Description', type: 'textarea' },
        { name: 'location', label: 'Location', type: 'text' },
        { name: 'event_date', label: 'Date', type: 'date' },
        { name: 'event_time', label: 'Time', type: 'text' },
        { name: 'category', label: 'Category', type: 'select', options: ['Technology', 'Workshop', 'Hackathon', 'Social', 'Seminar'] },
        { name: 'capacity', label: 'Capacity', type: 'number' },
        { name: 'organizer', label: 'Organizer', type: 'text' }
    ],
    contacts: [
        { name: 'first_name', label: 'First Name', type: 'text', required: true },
        { name: 'last_name', label: 'Last Name', type: 'text' },
        { name: 'email', label: 'Email', type: 'email' },
        { name: 'phone', label: 'Phone', type: 'text' },
        { name: 'company', label: 'Company', type: 'text' },
        { name: 'job_title', label: 'Job Title', type: 'text' },
        { name: 'city', label: 'City', type: 'text' },
        { name: 'country', label: 'Country', type: 'text' }
    ],
    songs: [
        { name: 'title', label: 'Title', type: 'text', required: true },
        { name: 'artist', label: 'Artist', type: 'text', required: true },
        { name: 'album', label: 'Album', type: 'text' },
        { name: 'genre', label: 'Genre', type: 'select', options: ['Rock', 'Pop', 'Hip Hop', 'R&B', 'Jazz', 'Classical', 'Electronic'] },
        { name: 'duration', label: 'Duration (sec)', type: 'number' },
        { name: 'year', label: 'Year', type: 'number' }
    ],
    quotes: [
        { name: 'text', label: 'Quote Text', type: 'textarea', required: true },
        { name: 'author', label: 'Author', type: 'text', required: true },
        { name: 'category', label: 'Category', type: 'select', options: ['Programming', 'Motivation', 'Wisdom', 'Science', 'Life'] }
    ],
    countries: [
        { name: 'name', label: 'Country Name', type: 'text', required: true },
        { name: 'capital', label: 'Capital', type: 'text' },
        { name: 'continent', label: 'Continent', type: 'select', options: ['Africa', 'Asia', 'Europe', 'North America', 'South America', 'Oceania'] },
        { name: 'population', label: 'Population', type: 'number' },
        { name: 'currency', label: 'Currency', type: 'text' }
    ],
    jokes: [
        { name: 'setup', label: 'Setup', type: 'textarea', required: true },
        { name: 'punchline', label: 'Punchline', type: 'textarea', required: true },
        { name: 'category', label: 'Category', type: 'select', options: ['programming', 'general', 'science', 'math'] }
    ],
    vehicles: [
        { name: 'make', label: 'Make', type: 'text', required: true },
        { name: 'model', label: 'Model', type: 'text', required: true },
        { name: 'year', label: 'Year', type: 'number' },
        { name: 'type', label: 'Type', type: 'select', options: ['Sedan', 'SUV', 'Truck', 'Coupe', 'Hatchback', 'Van'] },
        { name: 'color', label: 'Color', type: 'text' },
        { name: 'price', label: 'Price', type: 'number' },
        { name: 'fuel_type', label: 'Fuel', type: 'select', options: ['Gasoline', 'Electric', 'Hybrid', 'Diesel'] }
    ],
    courses: [
        { name: 'title', label: 'Title', type: 'text', required: true },
        { name: 'instructor', label: 'Instructor', type: 'text' },
        { name: 'category', label: 'Category', type: 'select', options: ['Programming', 'Web Dev', 'Data Science', 'AI & ML', 'DevOps', 'Security'] },
        { name: 'level', label: 'Level', type: 'select', options: ['beginner', 'intermediate', 'advanced'] },
        { name: 'duration_hours', label: 'Hours', type: 'number', step: '0.5' },
        { name: 'price', label: 'Price', type: 'number', step: '0.01' },
        { name: 'rating', label: 'Rating', type: 'number', step: '0.1' }
    ],
    pets: [
        { name: 'name', label: 'Name', type: 'text', required: true },
        { name: 'species', label: 'Species', type: 'select', options: ['Dog', 'Cat', 'Bird', 'Rabbit', 'Fish', 'Hamster'], required: true },
        { name: 'breed', label: 'Breed', type: 'text' },
        { name: 'age', label: 'Age', type: 'number' },
        { name: 'color', label: 'Color', type: 'text' },
        { name: 'weight', label: 'Weight (kg)', type: 'number', step: '0.1' },
        { name: 'shelter', label: 'Shelter', type: 'text' }
    ],
    weather: [],
    ai: []
};

const TABLE_COLUMNS = {
    books: ['id', 'title', 'author', 'genre', 'year', 'available', 'is_frozen'],
    menu: ['id', 'name', 'price', 'category', 'is_available', 'is_frozen'],
    tasks: ['id', 'title', 'status', 'priority', 'due_date', 'assigned_to', 'is_frozen'],
    students: ['id', 'name', 'email', 'student_id', 'major', 'gpa', 'is_frozen'],
    notes: ['id', 'title', 'category', 'is_pinned', 'is_frozen'],
    files: ['id', 'original_name', 'file_type', 'file_size', 'is_frozen'],
    blog: ['id', 'title', 'author', 'tags', 'is_published', 'is_frozen'],
    inventory: ['id', 'name', 'sku', 'quantity', 'price', 'category', 'is_frozen'],
    products: ['id', 'name', 'price', 'category', 'brand', 'rating', 'stock', 'is_frozen'],
    movies: ['id', 'title', 'director', 'genre', 'year', 'rating', 'runtime', 'is_frozen'],
    recipes: ['id', 'title', 'cuisine', 'difficulty', 'prep_time', 'cook_time', 'servings', 'is_frozen'],
    events: ['id', 'title', 'location', 'event_date', 'category', 'capacity', 'is_frozen'],
    contacts: ['id', 'first_name', 'last_name', 'email', 'company', 'country', 'is_frozen'],
    songs: ['id', 'title', 'artist', 'album', 'genre', 'duration', 'year', 'is_frozen'],
    quotes: ['id', 'text', 'author', 'category', 'is_frozen'],
    countries: ['id', 'name', 'capital', 'continent', 'population', 'currency', 'is_frozen'],
    jokes: ['id', 'setup', 'punchline', 'category', 'is_frozen'],
    vehicles: ['id', 'make', 'model', 'year', 'type', 'price', 'fuel_type', 'is_frozen'],
    courses: ['id', 'title', 'instructor', 'level', 'price', 'rating', 'is_frozen'],
    pets: ['id', 'name', 'species', 'breed', 'age', 'weight', 'adopted', 'is_frozen'],
    weather: ['city', 'country', 'temp', 'humidity', 'condition', 'wind_speed'],
    ai: []
};

function buildCurlExamples(moduleName, endpoint) {
    const B = BASE_URL;
    const E = endpoint;
    const std = [
        { method: 'GET', label: 'List all', cmd: 'curl ' + B + E },
        { method: 'GET', label: 'Get by ID', cmd: 'curl ' + B + E + '/1' },
        { method: 'POST', label: 'Create', cmd: 'curl -X POST ' + B + E + ' \\\n  -H "Content-Type: application/json" \\\n  -d \'{"example":"data"}\'' },
        { method: 'PUT', label: 'Update (needs key)', cmd: 'curl -X PUT ' + B + E + '/1 \\\n  -H "Content-Type: application/json" \\\n  -H "X-API-Key: nhk_YOUR_KEY" \\\n  -d \'{"field":"value"}\'' },
        { method: 'DELETE', label: 'Delete (needs key)', cmd: 'curl -X DELETE ' + B + E + '/1 \\\n  -H "X-API-Key: nhk_YOUR_KEY"' }
    ];
    const extras = {
        books: [{ method: 'GET', label: 'Search', cmd: 'curl "' + B + E + '?search=python"' }, { method: 'GET', label: 'Filter genre', cmd: 'curl "' + B + E + '?genre=Fiction"' }],
        menu: [{ method: 'GET', label: 'Filter category', cmd: 'curl "' + B + E + '?category=Main+Course"' }],
        tasks: [{ method: 'GET', label: 'Filter status', cmd: 'curl "' + B + E + '?status=pending"' }, { method: 'GET', label: 'Filter priority', cmd: 'curl "' + B + E + '?priority=high"' }],
        students: [{ method: 'GET', label: 'Filter major', cmd: 'curl "' + B + E + '?major=Computer+Science"' }],
        notes: [{ method: 'GET', label: 'Filter pinned', cmd: 'curl "' + B + E + '?is_pinned=1"' }],
        products: [{ method: 'GET', label: 'Top rated', cmd: 'curl ' + B + E + '/top-rated' }, { method: 'GET', label: 'Filter brand', cmd: 'curl "' + B + E + '?brand=Apple"' }],
        movies: [{ method: 'GET', label: 'Top rated', cmd: 'curl ' + B + E + '/top-rated' }, { method: 'GET', label: 'Filter genre', cmd: 'curl "' + B + E + '?genre=Sci-Fi"' }],
        recipes: [{ method: 'GET', label: 'Filter cuisine', cmd: 'curl "' + B + E + '?cuisine=Italian"' }],
        events: [{ method: 'GET', label: 'Upcoming', cmd: 'curl ' + B + E + '/upcoming' }],
        contacts: [{ method: 'GET', label: 'Search', cmd: 'curl "' + B + E + '?search=alice"' }],
        songs: [{ method: 'GET', label: 'Filter genre', cmd: 'curl "' + B + E + '?genre=Rock"' }],
        quotes: [{ method: 'GET', label: 'Random', cmd: 'curl ' + B + E + '/random' }],
        countries: [{ method: 'GET', label: 'By continent', cmd: 'curl ' + B + E + '/by-continent' }],
        jokes: [{ method: 'GET', label: 'Random', cmd: 'curl ' + B + E + '/random' }],
        vehicles: [{ method: 'GET', label: 'Filter type', cmd: 'curl "' + B + E + '?type=SUV"' }],
        courses: [{ method: 'GET', label: 'Free courses', cmd: 'curl ' + B + E + '/free' }, { method: 'GET', label: 'Popular', cmd: 'curl ' + B + E + '/popular' }],
        pets: [{ method: 'GET', label: 'Available', cmd: 'curl ' + B + E + '/available' }],
        files: [
            { method: 'GET', label: 'List files', cmd: 'curl ' + B + E },
            { method: 'POST', label: 'Upload', cmd: 'curl -X POST ' + B + E + '/upload \\\n  -F "file=@myfile.txt"' },
            { method: 'GET', label: 'Download', cmd: 'curl ' + B + E + '/download/1 -O' },
            { method: 'DELETE', label: 'Delete', cmd: 'curl -X DELETE ' + B + E + '/1 \\\n  -H "X-API-Key: nhk_YOUR_KEY"' }
        ],
        weather: [
            { method: 'GET', label: 'All cities', cmd: 'curl ' + B + '/api/weather' },
            { method: 'GET', label: 'Specific city', cmd: 'curl "' + B + '/api/weather?city=dubai"' },
            { method: 'GET', label: 'Compare', cmd: 'curl "' + B + '/api/weather/compare?city1=dubai&city2=london"' },
            { method: 'GET', label: 'Forecast', cmd: 'curl ' + B + '/api/weather/forecast/dubai' }
        ],
        ai: [
            { method: 'POST', label: 'Generate', cmd: 'curl -X POST ' + B + '/api/ai/generate \\\n  -H "Content-Type: application/json" \\\n  -H "X-API-Key: nai_YOUR_AI_KEY" \\\n  -d \'{"prompt":"Explain REST APIs"}\'' },
            { method: 'POST', label: 'Summarize', cmd: 'curl -X POST ' + B + '/api/ai/summarize \\\n  -H "Content-Type: application/json" \\\n  -H "X-API-Key: nai_YOUR_AI_KEY" \\\n  -d \'{"text":"Long text..."}\'' },
            { method: 'POST', label: 'Chat', cmd: 'curl -X POST ' + B + '/api/ai/chat \\\n  -H "Content-Type: application/json" \\\n  -H "X-API-Key: nai_YOUR_AI_KEY" \\\n  -d \'{"message":"What is HTTP?"}\'' },
            { method: 'POST', label: 'Classify', cmd: 'curl -X POST ' + B + '/api/ai/classify \\\n  -H "Content-Type: application/json" \\\n  -H "X-API-Key: nai_YOUR_AI_KEY" \\\n  -d \'{"text":"Great!","categories":["positive","negative"]}\'' }
        ]
    };
    if (['files', 'weather', 'ai'].includes(moduleName)) return extras[moduleName] || [];
    const ex = extras[moduleName] || [];
    return [...std.slice(0, 2), ...ex, ...std.slice(2)];
}
