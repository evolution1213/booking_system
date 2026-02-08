document.addEventListener('DOMContentLoaded', function() {
  console.debug('main.js loaded');
  const filterForm = document.querySelector('form#filter-form') || document.querySelector('form[method=get]');

  function getCookie(name) {
    const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return v ? v.pop() : '';
  }
  const roomsArea = document.getElementById('rooms-area');

  function fetchRooms(params = {}) {
    const spinner = document.getElementById('list-spinner');
    if (spinner) spinner.classList.remove('d-none');
    const url = new URL(window.location.href);
    Object.keys(params).forEach(k => url.searchParams.set(k, params[k]));
    // Keep existing filters
    const opts = {headers: {'X-Requested-With': 'XMLHttpRequest'}};
    fetch(url, opts).then(r => r.json()).then(data => {
      roomsArea.innerHTML = data.html;
      // Update browser URL (without reloading)
      window.history.replaceState({}, '', url);
      updateShowAllButton();
      if (spinner) spinner.classList.add('d-none');
    }).catch(err => { if (spinner) spinner.classList.add('d-none'); console.error(err); });
  }

  // Book-now button: populate sidebar select and scroll to it
  document.addEventListener('click', function(e) {
    const t = e.target.closest && e.target.closest('.book-now');
    if (t) {
      e.preventDefault();
      const roomId = t.getAttribute('data-room-id');
      const select = document.querySelector('select[name="room"]');
      if (select) {
        select.value = roomId;
        // scroll into view
        const sidebar = document.querySelector('.booking-sidebar');
        if (sidebar) sidebar.scrollIntoView({behavior: 'smooth', block: 'center'});
      }
    }
  });

  // Live filter submit
  if (filterForm) {
    filterForm.addEventListener('submit', function(e) {
      e.preventDefault();
      const formData = new FormData(filterForm);
      const params = {};
      for (let [k, v] of formData.entries()) if (v) params[k] = v;
      params.page = 1;
      fetchRooms(params);
    });
  }

  // Update show-all button at startup
  updateShowAllButton();

  // Load more handler (delegated)
  document.addEventListener('click', function(e) {
    if (e.target && e.target.id === 'load-more') {
      const next = e.target.getAttribute('data-next-page');
      const url = new URL(window.location.href);
      url.searchParams.set('page', next);
      const opts = {headers: {'X-Requested-With': 'XMLHttpRequest'}};
      fetch(url, opts).then(r => r.json()).then(data => {
        // Append new cards
        const temp = document.createElement('div');
        temp.innerHTML = data.html;
        const newGrid = temp.querySelector('#rooms-grid');
        const existing = document.querySelector('#rooms-grid');
        if (existing && newGrid) {
          existing.insertAdjacentHTML('beforeend', newGrid.innerHTML);
        }
        // Update or remove load-more button
        const btn = document.getElementById('load-more');
        if (data.has_next && btn) {
          // increment page
          const p = parseInt(next, 10) + 1;
          btn.setAttribute('data-next-page', p);
        } else if (btn) {
          btn.remove();
        }
      });
    }
  });



  // Map modal handling: initialize Leaflet map when modal is shown and handle map button clicks.
  const mapModalEl = document.getElementById('mapBookingModal');
  let mapInstance = null;
  let mapMarkers = [];
  let pendingCoords = null;
  let pendingMarkers = null;

  function clearMapMarkers() {
    if (!mapInstance) return;
    mapMarkers.forEach(m => mapInstance.removeLayer(m));
    mapMarkers = [];
  }

  if (mapModalEl) {
    mapModalEl.addEventListener('shown.bs.modal', function () {
      const container = document.getElementById('map-modal-container');
      console.debug('map modal shown', {pendingMarkersLength: pendingMarkers ? pendingMarkers.length : 0, pendingCoords});
      if (!container) { console.warn('map container missing'); return; }
      if (typeof L === 'undefined') { console.error('Leaflet (L) is undefined'); return; }

      // If we have a collection of markers (show-all), use them
      if (pendingMarkers && pendingMarkers.length) {
        const first = pendingMarkers[0];
        if (!mapInstance) {
          mapInstance = L.map(container).setView([first.lat, first.lng], 12);
          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(mapInstance);
        } else {
          mapInstance.setView([first.lat, first.lng], 12);
        }
        clearMapMarkers();
        const bounds = [];
        pendingMarkers.forEach(m => {
          const mk = L.marker([m.lat, m.lng]).addTo(mapInstance).bindPopup(m.name || 'Кімната');
          mapMarkers.push(mk);
          bounds.push([m.lat, m.lng]);
        });
        if (bounds.length > 1) mapInstance.fitBounds(bounds);
        else mapInstance.setView(bounds[0], 15);
        setTimeout(() => mapInstance.invalidateSize(), 100);
        pendingMarkers = null;
        return;
      }

      if (!pendingCoords) return;
      const {lat, lng} = pendingCoords;
      if (!mapInstance) {
        mapInstance = L.map(container).setView([lat, lng], 15);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(mapInstance);
        const mk = L.marker([lat, lng]).addTo(mapInstance);
        mapMarkers = [mk];
      } else {
        mapInstance.setView([lat, lng], 15);
        clearMapMarkers();
        const mk = L.marker([lat, lng]).addTo(mapInstance);
        mapMarkers = [mk];
        setTimeout(() => mapInstance.invalidateSize(), 100);
      }
    });
    mapModalEl.addEventListener('hidden.bs.modal', function () {
      pendingCoords = null;
      pendingMarkers = null;
    });
  }

  // Delegated clicks for showing map or booking from map
  document.addEventListener('click', function(e) {


    const mapBtn = e.target.closest && e.target.closest('.show-map');
    if (mapBtn) {
      e.preventDefault();
      console.debug('per-card show-map clicked', mapBtn.getAttribute('data-lat'), mapBtn.getAttribute('data-lng'));
      const lat = parseFloat(mapBtn.getAttribute('data-lat'));
      const lng = parseFloat(mapBtn.getAttribute('data-lng'));
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;
      pendingCoords = {lat, lng};
      const modal = new bootstrap.Modal(mapModalEl);
      modal.show();
      return;
    }

    const btn = e.target.closest && e.target.closest('.book-from-map');
    if (btn) {
      e.preventDefault();
      const roomId = btn.getAttribute('data-room-id');
      const mapBookingModal = new bootstrap.Modal(mapModalEl);
      const input = document.getElementById('map-modal-room-id');
      if (input) input.value = roomId;
      mapBookingModal.show();
    }
  });


  // --- New main map modal & toggle handling ---
  const showMapBtn = document.getElementById('show-map');
  const mapModalMainEl = document.getElementById('mapModal');
  let mapMainInstance = null;
  let markersLayer = null;
  let roomsCache = [];
  let markersCreated = false;
  let markersVisible = false;

  const roomsApiUrl = showMapBtn && showMapBtn.dataset && showMapBtn.dataset.roomsMapUrl ? showMapBtn.dataset.roomsMapUrl : '/rooms/api/rooms_map/';

  function createMarkersFromCacheMain() {
    if (!roomsCache.length || !mapMainInstance) return;
    if (!markersLayer) markersLayer = (L.markerClusterGroup ? L.markerClusterGroup() : L.layerGroup());
    if (markersLayer.clearLayers) markersLayer.clearLayers();
    else if (markersLayer.eachLayer) markersLayer.eachLayer(layer => layer.remove());

    const bounds = [];
    roomsCache.forEach(r => {
      if (r.lat != null && r.lng != null) {
        const marker = L.marker([r.lat, r.lng]);
        const popup = `<div><strong><a href="${r.url}">${r.name}</a></strong><br>${r.city || ''} ${r.type ? ('• ' + r.type) : ''}<br><strong>${r.price} грн/год</strong><br><button class="btn btn-sm btn-success mt-2 book-from-map" data-room-id="${r.id}">Бронювати</button></div>`;
        marker.bindPopup(popup);
        markersLayer.addLayer ? markersLayer.addLayer(marker) : marker.addTo(markersLayer);
        bounds.push([r.lat, r.lng]);
      }
    });
    markersCreated = true;
    if (bounds.length && mapMainInstance) mapMainInstance.fitBounds(bounds, {padding: [40, 40]});
  }

  function showMarkersMain() {
    if (!mapMainInstance) return;
    if (!markersCreated) createMarkersFromCacheMain();
    if (markersLayer && !mapMainInstance.hasLayer(markersLayer)) mapMainInstance.addLayer(markersLayer);
    markersVisible = true;
    const tbtn = document.getElementById('toggle-markers'); if (tbtn) tbtn.textContent = 'Приховати точки';
  }

  function hideMarkersMain() {
    if (!mapMainInstance || !markersLayer) return;
    if (mapMainInstance.hasLayer && mapMainInstance.hasLayer(markersLayer)) mapMainInstance.removeLayer(markersLayer);
    markersVisible = false;
    const tbtn = document.getElementById('toggle-markers'); if (tbtn) tbtn.textContent = 'Показати точки';
  }

  if (showMapBtn && mapModalMainEl) {
    showMapBtn.addEventListener('click', function(e) {
      e.preventDefault();
      const modal = new bootstrap.Modal(mapModalMainEl);
      modal.show();
      if (!mapMainInstance) {
        mapMainInstance = L.map('mapid').setView([49.0, 32.0], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap contributors' }).addTo(mapMainInstance);
      }
      // remove markers if they are hidden
      try { if (markersLayer && mapMainInstance.hasLayer && !markersVisible && mapMainInstance.hasLayer(markersLayer)) mapMainInstance.removeLayer(markersLayer); } catch (ex) { /*no-op*/ }
      setTimeout(function() { mapMainInstance.invalidateSize(); }, 260);
    });

    const toggleBtn = document.getElementById('toggle-markers');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', function(e) {
        e.preventDefault();
        if (!roomsCache.length) {
          fetch(roomsApiUrl, {headers: {'X-Requested-With': 'XMLHttpRequest'}})
            .then(r => { if (!r.ok) throw new Error('Network response was not ok: ' + r.status); return r.json(); })
            .then(data => { roomsCache = data.rooms || []; showMarkersMain(); })
            .catch(err => { console.error('Failed to load rooms for map:', err); alert('Не вдалося завантажити точки для мапи.'); });
          return;
        }
        if (!markersVisible) showMarkersMain(); else hideMarkersMain();
      });
    }
  }



});
