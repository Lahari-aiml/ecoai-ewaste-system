/**
 * EcoAI Web Application Client Scripts
 * Handles Leaflet Maps, Geolocation, Interactive Popups, and UI Enhancements.
 */

// Example prompts for quick classification testing
const SAMPLE_PROMPTS = [
    "My old laptop switches on, but its screen is damaged and has flickering lines.",
    "Fully functional Samsung Galaxy S10 with minor scratches on back, wiped and ready to donate.",
    "Burnt desktop motherboard from lightning power surge with melted capacitors and scorch marks.",
    "Washing machine control board shows sensor error code E03 and won't spin.",
    "Working Kindle Paperwhite with charger and case, great condition.",
    "Swollen lithium battery leaking chemical smell and bulging the casing."
];

let mapInstance = null;
let providerMarkers = [];
let userMarker = null;
let radiusCircle = null;

document.addEventListener('DOMContentLoaded', function () {
    // 1. Auto-dismiss flash messages after 6 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            try {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                bsAlert.close();
            } catch (e) {}
        }, 6000);
    });

    // 2. Sample Prompt Injector for Classify Page
    const sampleBtn = document.getElementById('btn-try-sample');
    const descInput = document.getElementById('item-description');
    if (sampleBtn && descInput) {
        sampleBtn.addEventListener('click', function () {
            const randomSample = SAMPLE_PROMPTS[Math.floor(Math.random() * SAMPLE_PROMPTS.length)];
            descInput.value = randomSample;
            descInput.focus();
        });
    }

    // 3. Geolocation Permission Handler on Providers Page
    const btnGetLocation = document.getElementById('btn-get-location');
    if (btnGetLocation) {
        btnGetLocation.addEventListener('click', function () {
            requestUserGeolocation();
        });
    }
});

/**
 * Request user's device coordinates using browser Geolocation API
 */
function requestUserGeolocation() {
    const statusBox = document.getElementById('location-status');
    const latInput = document.getElementById('user-lat');
    const lonInput = document.getElementById('user-lon');
    const form = document.getElementById('provider-search-form');

    if (!navigator.geolocation) {
        if (statusBox) {
            statusBox.innerHTML = '<div class="alert alert-warning py-2 mb-2"><i class="bi bi-exclamation-triangle-fill me-1"></i> Geolocation is not supported by your browser. Please select a city manually.</div>';
        }
        return;
    }

    if (statusBox) {
        statusBox.innerHTML = '<div class="text-primary py-1"><span class="spinner-border spinner-border-sm me-2"></span>Requesting GPS coordinates with your permission...</div>';
    }

    navigator.geolocation.getCurrentPosition(
        function (position) {
            const lat = position.coords.latitude.toFixed(6);
            const lon = position.coords.longitude.toFixed(6);

            if (latInput) latInput.value = lat;
            if (lonInput) lonInput.value = lon;

            if (statusBox) {
                statusBox.innerHTML = '<div class="text-success py-1"><i class="bi bi-geo-alt-fill me-1"></i> Location detected! Searching nearby providers...</div>';
            }

            if (form) {
                form.submit();
            }
        },
        function (error) {
            let msg = "Location access was denied. Please select your city from the dropdown.";
            if (error.code === error.POSITION_UNAVAILABLE) {
                msg = "Location information is unavailable. Please select your city manually.";
            } else if (error.code === error.TIMEOUT) {
                msg = "The request to get user location timed out. Please select your city manually.";
            }
            if (statusBox) {
                statusBox.innerHTML = `<div class="alert alert-warning py-2 mb-2"><i class="bi bi-info-circle me-1"></i> ${msg}</div>`;
            }
        },
        { enableHighAccuracy: true, timeout: 8000, maximumAge: 60000 }
    );
}

/**
 * Initialize Leaflet OpenStreetMap with providers and search radius
 */
function initProvidersMap(mapId, userLat, userLon, providersData, radiusKm) {
    const mapElement = document.getElementById(mapId);
    if (!mapElement) return;

    const centerLat = userLat || 12.9716;
    const centerLon = userLon || 77.5946;

    mapInstance = L.map(mapId).setView([centerLat, centerLon], 11);

    // OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 18
    }).addTo(mapInstance);

    // Add User location marker if coordinates exist
    if (userLat && userLon) {
        const userIcon = L.divIcon({
            className: 'user-pin-icon',
            html: '<div style="background:#059669; color:#fff; width:34px; height:34px; border-radius:50%; display:flex; align-items:center; justify-content:center; border:3px solid #fff; box-shadow:0 0 12px rgba(5,150,105,0.6);"><i class="bi bi-person-fill" style="font-size:1.1rem;"></i></div>',
            iconSize: [34, 34],
            iconAnchor: [17, 17]
        });

        userMarker = L.marker([userLat, userLon], { icon: userIcon }).addTo(mapInstance)
            .bindPopup('<strong><i class="bi bi-geo-alt"></i> Your Detected Location</strong><br><small>Center of search radius</small>')
            .openPopup();

        // Draw Search Radius Circle
        if (radiusKm) {
            radiusCircle = L.circle([userLat, userLon], {
                radius: radiusKm * 1000,
                color: '#10b981',
                fillColor: '#10b981',
                fillOpacity: 0.08,
                weight: 1.5,
                dashArray: '4, 6'
            }).addTo(mapInstance);
        }
    }

    // Category marker colors
    const colorMap = {
        'Repair': { bg: '#2563eb', icon: 'bi-tools' },
        'Reuse': { bg: '#059669', icon: 'bi-arrow-repeat' },
        'Recycle': { bg: '#dc2626', icon: 'bi-recycle' }
    };

    // Plot Provider Markers
    providerMarkers = [];
    const bounds = [];
    if (userLat && userLon) bounds.push([userLat, userLon]);

    if (Array.isArray(providersData)) {
        providersData.forEach(function (p, index) {
            const meta = colorMap[p.category_name] || { bg: '#059669', icon: 'bi-building' };
            const markerIcon = L.divIcon({
                className: 'provider-pin-icon',
                html: `<div style="background:${meta.bg}; color:#fff; width:36px; height:36px; border-radius:50%; display:flex; align-items:center; justify-content:center; border:2.5px solid #fff; box-shadow:0 3px 8px rgba(0,0,0,0.25); cursor:pointer;"><i class="bi ${meta.icon}"></i></div>`,
                iconSize: [36, 36],
                iconAnchor: [18, 18]
            });

            const marker = L.marker([p.latitude, p.longitude], { icon: markerIcon }).addTo(mapInstance);

            const pickupBadge = p.offers_pickup_bool
                ? '<span class="badge bg-success-subtle text-success border border-success-subtle mb-1"><i class="bi bi-truck me-1"></i> Offers Doorstep Pickup</span>'
                : '<span class="badge bg-secondary-subtle text-secondary border border-secondary-subtle mb-1">In-person drop-off</span>';

            const popupHtml = `
                <div style="min-width:210px; font-family:'Plus Jakarta Sans',sans-serif;">
                    <div class="fw-bold mb-1" style="font-size:0.95rem; color:#0f172a;">${p.name}</div>
                    <div class="mb-1">${pickupBadge}</div>
                    <div class="small text-muted mb-1"><i class="bi bi-geo-alt"></i> ${p.address}, ${p.city}</div>
                    <div class="small fw-semibold text-primary mb-2"><i class="bi bi-telephone"></i> ${p.phone}</div>
                    ${p.distance_formatted ? `<div class="small text-secondary mb-2"><i class="bi bi-signpost-2"></i> ${p.distance_formatted} approx.</div>` : ''}
                    <div class="d-flex gap-1 mt-2">
                        ${p.offers_pickup_bool ? `<a href="/pickup/request/${p.id}" class="btn btn-sm btn-success text-white py-1 px-2" style="font-size:0.8rem;"><i class="bi bi-truck"></i> Request Pickup</a>` : ''}
                        <a href="tel:${p.phone}" class="btn btn-sm btn-outline-secondary py-1 px-2" style="font-size:0.8rem;"><i class="bi bi-telephone"></i> Call</a>
                    </div>
                </div>
            `;

            marker.bindPopup(popupHtml);
            providerMarkers.push({ id: p.id, marker: marker });
            bounds.push([p.latitude, p.longitude]);
        });
    }

    if (bounds.length > 1) {
        mapInstance.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
    }
}

/**
 * Pan map and open popup when provider card is clicked
 */
function focusProviderOnMap(providerId, lat, lon) {
    if (!mapInstance) return;
    mapInstance.setView([lat, lon], 14, { animate: true });
    const target = providerMarkers.find(m => m.id === providerId);
    if (target && target.marker) {
        target.marker.openPopup();
    }
}
