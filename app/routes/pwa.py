"""Rotas para PWA — manifest e service worker."""
from flask import Blueprint, send_from_directory, jsonify
import os

pwa_bp = Blueprint("pwa", __name__)


@pwa_bp.route("/manifest.json")
def manifest():
    return jsonify({
        "name": "ImobFlow",
        "short_name": "ImobFlow",
        "description": "Gestão de condomínios e imóveis",
        "start_url": "/dashboard",
        "display": "standalone",
        "background_color": "#0D1117",
        "theme_color": "#00D4AA",
        "orientation": "portrait-primary",
        "icons": [
            {"src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
        "categories": ["finance", "business"],
        "lang": "pt-BR",
    })


@pwa_bp.route("/sw.js")
def service_worker():
    """Service worker — cache offline das páginas principais."""
    sw_content = """
const CACHE_NAME = 'imobflow-v1';
const URLS_TO_CACHE = [
  '/',
  '/dashboard',
  '/static/css/style.css',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(URLS_TO_CACHE))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    caches.match(event.request).then(cached => {
      const networkFetch = fetch(event.request).then(response => {
        if (response && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      });
      return cached || networkFetch;
    })
  );
});
"""
    from flask import Response
    return Response(sw_content, mimetype="application/javascript")
