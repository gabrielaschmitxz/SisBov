// Service Worker básico para PWA
const CACHE_NAME = 'sisbov-v2';
const urlsToCache = [
    '/static/css/style.css',
    '/static/js/app.js',
    '/static/manifest.json'
];

// Instalar Service Worker
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                return cache.addAll(urlsToCache);
            })
    );
    // Força a ativação imediata
    self.skipWaiting();
});

// Ativar Service Worker
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    // Assume controle imediato de todas as páginas
    return self.clients.claim();
});

// Interceptar requisições
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);
    
    // Para requisições de navegação (páginas HTML), sempre buscar da rede primeiro
    if (event.request.mode === 'navigate') {
        event.respondWith(
            fetch(event.request)
                .then((response) => {
                    // Se a requisição foi bem-sucedida, retornar
                    return response;
                })
                .catch(() => {
                    // Se falhar, tentar do cache (offline)
                    return caches.match(event.request);
                })
        );
        return;
    }
    
    // Para recursos estáticos (CSS, JS, imagens), usar cache-first
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(event.request)
                .then((response) => {
                    // Retornar do cache se disponível
                    if (response) {
                        return response;
                    }
                    // Caso contrário, buscar da rede e cachear
                    return fetch(event.request).then((response) => {
                        // Só cachear se a resposta foi bem-sucedida
                        if (response.status === 200) {
                            const responseToCache = response.clone();
                            caches.open(CACHE_NAME).then((cache) => {
                                cache.put(event.request, responseToCache);
                            });
                        }
                        return response;
                    });
                })
        );
        return;
    }
    
    // Para requisições de API, sempre buscar da rede
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(fetch(event.request));
        return;
    }
    
    // Para outras requisições, buscar da rede primeiro
    event.respondWith(
        fetch(event.request)
            .catch(() => {
                // Se falhar, tentar do cache
                return caches.match(event.request);
            })
    );
});

