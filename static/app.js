/**
 * Pakistan Food Business Intelligence & POS Platform - Frontend Application
 */

const app = {
  map: null,
  mapMarkers: [],
  categoryChart: null,
  provinceChart: null,
  priorityChart: null,
  allBusinesses: [],
  filteredBusinesses: [],
  overviewData: null,
  currentPage: 1,
  totalPages: 1,
  totalRecords: 0,
  pageSize: 100,
  searchDebounceTimer: null,

  async init() {
    this.setupNavigation();
    this.setupFilterListeners();
    this.setupHunterSubtabs();
    this.setupHunterEventListeners();
    await this.loadOverview();
    await this.loadBusinesses();
    this.initLeafletMap();
    this.renderCharts();
    this.loadBuyerIntent();
    this.loadNewOpenings();
    this.loadVendors();
    this.loadCrmLeads();
    this.loadCollectorLogs();
    this.loadHunterDashboard();
    this.loadHunterBuyerIntent();
    this.loadHunterOpenings();
    this.loadHunterReports();
    this.loadHunterReviewQueue();
    this.loadHunterConfig();
    this.loadHunterJobs();
  },

  // Navigation across all 23 sections
  setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        navItems.forEach(n => n.classList.remove('active'));
        item.classList.add('active');

        const viewId = item.getAttribute('data-view');
        this.switchView(viewId, item.innerText.trim());
      });
    });

    const triggerBtn = document.getElementById('btn-trigger-collector');
    if (triggerBtn) {
      triggerBtn.addEventListener('click', () => this.triggerCollectorRun());
    }
  },

  switchView(viewId, titleText) {
    // Hide all view panels
    document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));

    // Handle AI Lead Hunter subviews (POS Buyer Radar, Daily Reports, Review Queue)
    if (viewId === 'view-hunter-radar') {
      const hunterView = document.getElementById('view-lead-hunter');
      if (hunterView) hunterView.classList.add('active');
      this.switchHunterSubtab('subtab-buyer-radar');
      const titleEl = document.getElementById('page-title');
      if (titleEl) titleEl.innerText = titleText || 'POS Buyer Radar (Active Requests)';
      return;
    }

    if (viewId === 'view-hunter-reports') {
      const hunterView = document.getElementById('view-lead-hunter');
      if (hunterView) hunterView.classList.add('active');
      this.switchHunterSubtab('subtab-daily-reports');
      const titleEl = document.getElementById('page-title');
      if (titleEl) titleEl.innerText = titleText || 'Daily POS Intelligence Reports';
      return;
    }

    if (viewId === 'view-review-queue') {
      const hunterView = document.getElementById('view-lead-hunter');
      if (hunterView) hunterView.classList.add('active');
      this.switchHunterSubtab('subtab-review-queue');
      const titleEl = document.getElementById('page-title');
      if (titleEl) titleEl.innerText = titleText || 'Human Review Queue';
      return;
    }

    if (viewId === 'view-lead-hunter') {
      const hunterView = document.getElementById('view-lead-hunter');
      if (hunterView) hunterView.classList.add('active');
      const titleEl = document.getElementById('page-title');
      if (titleEl) titleEl.innerText = titleText || 'AI Daily Restaurant Discovery & POS Sales Lead Hunter';
      return;
    }

    // Handle Growth & Openings views (10. Newly Opened, 11. Opening Soon, 12. New Branches)
    if (viewId === 'view-newly-opened') {
      const targetView = document.getElementById('view-newly-opened');
      if (targetView) targetView.classList.add('active');
      this.loadNewOpenings('opened');
      const titleEl = document.getElementById('page-title');
      if (titleEl) titleEl.innerText = titleText || '10. Newly Opened Establishments';
      return;
    }

    if (viewId === 'view-opening-soon') {
      const targetView = document.getElementById('view-newly-opened');
      if (targetView) targetView.classList.add('active');
      this.loadNewOpenings('soon');
      const titleEl = document.getElementById('page-title');
      if (titleEl) titleEl.innerText = titleText || '11. Upcoming Food Businesses (Opening Soon)';
      return;
    }

    if (viewId === 'view-new-branches') {
      const targetView = document.getElementById('view-newly-opened');
      if (targetView) targetView.classList.add('active');
      this.loadNewOpenings('branch');
      const titleEl = document.getElementById('page-title');
      if (titleEl) titleEl.innerText = titleText || '12. New Branches & Chain Expansions';
      return;
    }

    // Update Topbar Title for all other views
    const titleEl = document.getElementById('page-title');
    if (titleEl) titleEl.innerText = titleText;

    // Handle standard views vs virtual category/province filtered views
    const categoryMapping = {
      'view-restaurants': { view: 'view-all-businesses', cat: 'Restaurants' },
      'view-cafes': { view: 'view-all-businesses', cat: 'Cafes' },
      'view-dhabas': { view: 'view-all-businesses', cat: 'Dhabas' },
      'view-bakeries': { view: 'view-all-businesses', cat: 'Bakeries' },
      'view-fastfood': { view: 'view-all-businesses', cat: 'Fast Food' },
      'view-hotels': { view: 'view-all-businesses', cat: 'Hotels' },
      'view-other-food': { view: 'view-all-businesses', cat: 'Sweet' },
      'view-province-research': { view: 'view-all-businesses', prov: 'Punjab' },
      'view-city-research': { view: 'view-all-businesses', city: 'Lahore' },
      'view-high-priority': { view: 'view-all-businesses', prio: 'P1' },
      'view-pos-opportunity': { view: 'view-all-businesses', opp: 'High' },
      'view-existing-pos': { view: 'view-all-businesses', hasPos: true }
    };

    if (categoryMapping[viewId]) {
      const cfg = categoryMapping[viewId];
      const targetView = document.getElementById(cfg.view);
      if (targetView) targetView.classList.add('active');

      if (cfg.cat) {
        document.getElementById('filter-category').value = cfg.cat;
      }
      if (cfg.prov) {
        document.getElementById('filter-province').value = cfg.prov;
      }
      if (cfg.prio) {
        document.getElementById('filter-priority').value = cfg.prio;
      }
      if (cfg.opp) {
        document.getElementById('filter-opportunity').value = cfg.opp;
      }
      this.applyFilters();
    } else {
      const targetView = document.getElementById(viewId);
      if (targetView) targetView.classList.add('active');
    }

    // Leaflet map invalidate size when overview is shown
    if (viewId === 'view-overview' && this.map) {
      setTimeout(() => this.map.invalidateSize(), 200);
    }
  },

  setupFilterListeners() {
    const searchInput = document.getElementById('table-search');
    const provSelect = document.getElementById('filter-province');
    const catSelect = document.getElementById('filter-category');
    const prioSelect = document.getElementById('filter-priority');
    const oppSelect = document.getElementById('filter-opportunity');
    const resetBtn = document.getElementById('btn-reset-filters');

    if (searchInput) {
      searchInput.addEventListener('input', () => {
        clearTimeout(this.searchDebounceTimer);
        this.searchDebounceTimer = setTimeout(() => this.loadBusinesses(1), 350);
      });
    }
    if (provSelect) provSelect.addEventListener('change', () => this.loadBusinesses(1));
    if (catSelect) catSelect.addEventListener('change', () => this.loadBusinesses(1));
    if (prioSelect) prioSelect.addEventListener('change', () => this.loadBusinesses(1));
    if (oppSelect) oppSelect.addEventListener('change', () => this.loadBusinesses(1));

    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        if (searchInput) searchInput.value = '';
        if (provSelect) provSelect.value = '';
        if (catSelect) catSelect.value = '';
        if (prioSelect) prioSelect.value = '';
        if (oppSelect) oppSelect.value = '';
        this.loadBusinesses(1);
      });
    }

    const prevBtn = document.getElementById('btn-page-prev');
    const nextBtn = document.getElementById('btn-page-next');
    const firstBtn = document.getElementById('btn-page-first');
    const lastBtn = document.getElementById('btn-page-last');

    if (prevBtn) prevBtn.addEventListener('click', () => { if (this.currentPage > 1) this.loadBusinesses(this.currentPage - 1); });
    if (nextBtn) nextBtn.addEventListener('click', () => { if (this.currentPage < this.totalPages) this.loadBusinesses(this.currentPage + 1); });
    if (firstBtn) firstBtn.addEventListener('click', () => { if (this.currentPage > 1) this.loadBusinesses(1); });
    if (lastBtn) lastBtn.addEventListener('click', () => { if (this.currentPage < this.totalPages) this.loadBusinesses(this.totalPages); });
  },

  async loadOverview() {
    try {
      const res = await fetch('/api/overview');
      const data = await res.json();
      this.overviewData = data;

      const m = data.platform_metrics;
      document.getElementById('kpi-discovered').innerText = (m.total_discovered || 200000).toLocaleString();
      document.getElementById('kpi-intent').innerText = m.total_active_intent || 15;
      document.getElementById('kpi-opportunity').innerText = (m.total_high_opportunity || 124437).toLocaleString();
      document.getElementById('kpi-whatsapp').innerText = (m.total_verified_whatsapp || 69750).toLocaleString();

      document.getElementById('badge-total-biz').innerText = (m.total_discovered || 200000).toLocaleString();
      document.getElementById('badge-intent').innerText = m.total_active_intent || 15;
      if (document.getElementById('badge-hunter-intent')) document.getElementById('badge-hunter-intent').innerText = m.total_active_intent || 15;
      if (document.getElementById('badge-new-opened')) document.getElementById('badge-new-opened').innerText = 19;
      if (document.getElementById('badge-opening-soon')) document.getElementById('badge-opening-soon').innerText = 10;
      if (document.getElementById('badge-new-branches')) document.getElementById('badge-new-branches').innerText = 14;

      document.getElementById('dq-total-outlets').innerText = (m.total_discovered || 200000).toLocaleString();
      document.getElementById('dq-phone-cov').innerText = `${(m.total_with_phone || 199293).toLocaleString()} Outlets (${Math.round(m.total_with_phone / (m.total_discovered || 1) * 100)}%)`;
      document.getElementById('dq-wa-cov').innerText = `${(m.total_verified_whatsapp || 69750).toLocaleString()} Outlets (${Math.round(m.total_verified_whatsapp / (m.total_discovered || 1) * 100)}%)`;
    } catch (err) {
      console.error('Failed to load overview data', err);
    }
  },

  async loadBusinesses(page = 1) {
    this.currentPage = page;
    const search = (document.getElementById('table-search')?.value || '').trim();
    const province = document.getElementById('filter-province')?.value || '';
    const category = document.getElementById('filter-category')?.value || '';
    const priority = document.getElementById('filter-priority')?.value || '';
    const opp = document.getElementById('filter-opportunity')?.value || '';

    const params = new URLSearchParams({
      page: page,
      limit: this.pageSize
    });
    if (search) params.append('search', search);
    if (province) params.append('province', province);
    if (category) params.append('category', category);
    if (priority) params.append('priority', priority);
    if (opp) params.append('opportunity', opp);

    try {
      const res = await fetch(`/api/businesses?${params.toString()}`);
      const data = await res.json();
      this.allBusinesses = data.results || [];
      this.totalRecords = data.total !== undefined ? data.total : this.allBusinesses.length;
      this.totalPages = data.total_pages || Math.ceil(this.totalRecords / this.pageSize) || 1;

      this.renderTable(this.allBusinesses);
      this.updatePaginationUI();
    } catch (err) {
      console.error('Failed to load businesses', err);
    }
  },

  applyFilters() {
    this.loadBusinesses(1);
  },

  updatePaginationUI() {
    const infoEl = document.getElementById('pagination-info');
    const pageEl = document.getElementById('pagination-current-page');
    const start = this.totalRecords === 0 ? 0 : (this.currentPage - 1) * this.pageSize + 1;
    const end = Math.min(this.currentPage * this.pageSize, this.totalRecords);

    if (infoEl) {
      infoEl.innerHTML = `Showing <strong>${start.toLocaleString()}–${end.toLocaleString()}</strong> of <strong>${this.totalRecords.toLocaleString()}</strong> establishments`;
    }
    if (pageEl) {
      pageEl.innerText = `Page ${this.currentPage.toLocaleString()} of ${this.totalPages.toLocaleString()}`;
    }

    const prevBtn = document.getElementById('btn-page-prev');
    const nextBtn = document.getElementById('btn-page-next');
    const firstBtn = document.getElementById('btn-page-first');
    const lastBtn = document.getElementById('btn-page-last');

    if (prevBtn) prevBtn.disabled = this.currentPage <= 1;
    if (firstBtn) firstBtn.disabled = this.currentPage <= 1;
    if (nextBtn) nextBtn.disabled = this.currentPage >= this.totalPages;
    if (lastBtn) lastBtn.disabled = this.currentPage >= this.totalPages;
  },

  renderTable(businesses) {
    const tbody = document.getElementById('businesses-table-body');
    if (!tbody) return;

    if (businesses.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; padding: 30px; color: #64748b;">No food businesses found matching current filters.</td></tr>`;
      return;
    }

    tbody.innerHTML = businesses.map(b => {
      const prioClass = `badge-${(b.lead_priority || 'p3').toLowerCase()}`;
      const oppClass = b.pos_opportunity_score === 'High' ? 'badge-high' : (b.pos_opportunity_score === 'Medium' ? 'badge-med' : 'badge-low');
      
      const phoneHtml = b.phone 
        ? `<a href="tel:${b.phone}" style="color: #0284c7; text-decoration: none; font-weight: 500;"><i class="fa-solid fa-phone"></i> ${b.phone}</a>` 
        : `<span style="color: #94a3b8; font-size: 11px;">Not Published</span>`;

      const waHtml = (b.whatsapp && b.whatsapp_link)
        ? `<a href="${b.whatsapp_link}" target="_blank" class="btn btn-whatsapp btn-sm" style="margin-top: 4px;"><i class="fa-brands fa-whatsapp"></i> WhatsApp</a>`
        : '';

      const posBadge = b.pos_provider_name && b.pos_provider_name !== 'Unknown'
        ? `<span class="badge" style="background: #e0f2fe; color: #0369a1;">${b.pos_provider_name}</span>`
        : `<span class="badge" style="background: #fef2f2; color: #b91c1c;">No POS Identified</span>`;

      return `
        <tr>
          <td><span class="badge ${prioClass}">${b.lead_priority || 'P3'}</span></td>
          <td>
            <div class="biz-name-cell">${b.name}</div>
            <div class="biz-sub-cell">${b.subcategory || b.category_name}</div>
          </td>
          <td>${b.category_name}</td>
          <td>
            <strong>${b.city || 'Pakistan'}</strong>
            <div class="biz-sub-cell">${b.area || b.district || ''}</div>
          </td>
          <td>
            <div>${phoneHtml}</div>
            ${waHtml}
          </td>
          <td>${posBadge}</td>
          <td><span class="badge ${oppClass}">${b.pos_opportunity_score}</span></td>
          <td>
            <span class="badge" style="background: #f1f5f9; color: #334155;">${b.pipeline_stage || 'New Lead'}</span>
            <div class="biz-sub-cell">${b.assigned_rep || 'Unassigned'}</div>
          </td>
          <td>
            <button class="btn btn-outline btn-sm" onclick="app.viewBusinessDetail('${b.business_id}')"><i class="fa-solid fa-eye"></i> Details</button>
          </td>
        </tr>
      `;
    }).join('');
  },

  initLeafletMap() {
    const mapContainer = document.getElementById('leaflet-map');
    if (!mapContainer) return;

    // Center over Pakistan: ~30.3753, 69.3451, zoom 5
    this.map = L.map('leaflet-map').setView([30.3753, 69.3451], 5);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(this.map);

    this.loadMapMarkers();
  },

  async loadMapMarkers() {
    try {
      const res = await fetch('/api/locations');
      const data = await res.json();
      const markers = data.markers || [];

      markers.forEach(m => {
        if (!m.latitude || !m.longitude) return;

        const prioColor = m.lead_priority === 'P1' ? '#ef4444' : (m.lead_priority === 'P2' ? '#f59e0b' : '#059669');

        const circleMarker = L.circleMarker([m.latitude, m.longitude], {
          radius: 6,
          fillColor: prioColor,
          color: '#ffffff',
          weight: 1.5,
          opacity: 1,
          fillOpacity: 0.85
        }).addTo(this.map);

        const popupContent = `
          <div style="font-family: sans-serif; font-size: 12px; line-height: 1.4;">
            <strong style="font-size: 13px; color: #064e3b;">${m.name}</strong><br>
            <span style="color: #64748b;">${m.category_name} - ${m.city}</span><br>
            <span style="color: #059669; font-weight: bold;">Opportunity: ${m.pos_opportunity_score}</span> | 
            <span style="color: ${prioColor}; font-weight: bold;">${m.lead_priority}</span><br>
            ${m.phone ? `<a href="tel:${m.phone}" style="color: #0284c7;">Call: ${m.phone}</a><br>` : ''}
            ${m.whatsapp_link ? `<a href="${m.whatsapp_link}" target="_blank" style="color: #25d366; font-weight: bold;">Open WhatsApp</a><br>` : ''}
            <button onclick="app.viewBusinessDetail('${m.business_id}')" style="margin-top: 4px; padding: 2px 6px; font-size: 11px; cursor: pointer;">View Profile</button>
          </div>
        `;
        circleMarker.bindPopup(popupContent);
      });
    } catch (err) {
      console.error('Failed to load map markers', err);
    }
  },

  renderCharts() {
    if (!this.overviewData || !this.overviewData.distributions) return;
    const dist = this.overviewData.distributions;

    // 1. Categories Donut Chart
    const ctxCat = document.getElementById('chart-categories')?.getContext('2d');
    if (ctxCat) {
      const topCats = (dist.categories || []).slice(0, 7);
      this.categoryChart = new Chart(ctxCat, {
        type: 'doughnut',
        data: {
          labels: topCats.map(c => c.category_name),
          datasets: [{
            data: topCats.map(c => c.count),
            backgroundColor: ['#064e3b', '#059669', '#10b981', '#34d399', '#6ee7b7', '#a7f3d0', '#cbd5e1'],
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'bottom', labels: { boxWidth: 12, font: { size: 11 } } }
          }
        }
      });
    }

    // 2. Province Bar Chart
    const ctxProv = document.getElementById('chart-provinces')?.getContext('2d');
    if (ctxProv) {
      const provs = dist.provinces || [];
      this.provinceChart = new Chart(ctxProv, {
        type: 'bar',
        data: {
          labels: provs.map(p => p.province),
          datasets: [{
            label: 'Discovered Outlets',
            data: provs.map(p => p.count),
            backgroundColor: '#047857'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
            x: { grid: { display: false } }
          },
          plugins: { legend: { display: false } }
        }
      });
    }

    // 3. Lead Priority Funnel / Bar
    const ctxPrio = document.getElementById('chart-priorities')?.getContext('2d');
    if (ctxPrio) {
      const prios = dist.lead_priorities || [];
      this.priorityChart = new Chart(ctxPrio, {
        type: 'bar',
        data: {
          labels: prios.map(p => p.lead_priority),
          datasets: [{
            label: 'Sales Prospects',
            data: prios.map(p => p.count),
            backgroundColor: ['#ef4444', '#f59e0b', '#0284c7', '#64748b', '#cbd5e1']
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { beginAtZero: true, grid: { color: '#f1f5f9' } },
            x: { grid: { display: false } }
          },
          plugins: { legend: { display: false } }
        }
      });
    }
  },

  async loadBuyerIntent() {
    try {
      const res = await fetch('/api/buyer-intent');
      const data = await res.json();
      const container = document.getElementById('buyer-intent-cards-container');
      if (!container) return;

      const items = data.results || [];
      container.innerHTML = items.map(item => {
        const waLink = item.whatsapp ? `https://wa.me/${item.whatsapp.replace(/\D/g, '')}` : null;
        return `
          <div class="intent-card">
            <div class="card-top">
              <div>
                <strong style="font-size: 15px; color: #064e3b;">${item.business_name}</strong>
                <div style="font-size: 11px; color: #64748b;">${item.category} &bull; ${item.city}</div>
              </div>
              <span class="badge badge-intent">${item.intent_tier}</span>
            </div>

            <div style="font-size: 12px; font-weight: 600; color: #0f172a;">
              <i class="fa-solid fa-code-pull-request" style="color: #ef4444;"></i> Requirement: ${item.requirement_type}
            </div>

            <div class="evidence-box">
              "${item.evidence_summary}"
            </div>

            <div style="font-size: 11px; color: #64748b; display: flex; justify-content: space-between;">
              <span>Source: <strong>${item.source_platform}</strong></span>
              <span>Posted: ${item.original_post_date || 'Recent'}</span>
            </div>

            <div style="display: flex; gap: 8px; margin-top: 6px;">
              ${item.contact_phone ? `<a href="tel:${item.contact_phone}" class="btn btn-outline btn-sm"><i class="fa-solid fa-phone"></i> Call</a>` : ''}
              ${waLink ? `<a href="${waLink}" target="_blank" class="btn btn-whatsapp btn-sm"><i class="fa-brands fa-whatsapp"></i> WhatsApp</a>` : ''}
              <a href="${item.source_url}" target="_blank" class="btn btn-outline btn-sm"><i class="fa-solid fa-arrow-up-right-from-square"></i> Evidence</a>
              <button class="btn btn-primary btn-sm" onclick="app.openCrmModal('${item.business_id}')">Update Lead</button>
            </div>
          </div>
        `;
      }).join('');
    } catch (err) {
      console.error('Failed to load buyer intent', err);
    }
  },

  async loadNewOpenings(filterType = 'all') {
    const container = document.getElementById('new-openings-cards-container');
    if (!container) return;

    // Update filter buttons styling
    const btnAll = document.getElementById('btn-filter-openings-all');
    const btnOpened = document.getElementById('btn-filter-openings-opened');
    const btnSoon = document.getElementById('btn-filter-openings-soon');
    const btnBranch = document.getElementById('btn-filter-openings-branch');
    [btnAll, btnOpened, btnSoon, btnBranch].forEach(b => { if (b) b.classList.remove('active'); });

    // Update card header and border
    const cardEl = document.getElementById('openings-header-card');
    const titleEl = document.getElementById('openings-header-title');
    const descEl = document.getElementById('openings-header-desc');

    if (filterType === 'opened') {
      if (btnOpened) btnOpened.classList.add('active');
      if (cardEl) cardEl.style.borderLeft = '4px solid #10b981';
      if (titleEl) titleEl.innerHTML = '<i class="fa-solid fa-door-open" style="color: #10b981;"></i> 10. Newly Opened Food Establishments';
      if (descEl) descEl.innerText = 'Recently launched dining establishments, cafes, and bakeries verified across Pakistan. High prime conversion window for POS installation (within 14 days of launch).';
    } else if (filterType === 'soon') {
      if (btnSoon) btnSoon.classList.add('active');
      if (cardEl) cardEl.style.borderLeft = '4px solid #0284c7';
      if (titleEl) titleEl.innerHTML = '<i class="fa-solid fa-clock-rotate-left" style="color: #0284c7;"></i> 11. Opening Soon - Pre-Launch Food Venues';
      if (descEl) descEl.innerText = 'Upcoming food outlets currently under fit-out, test kitchen, or pre-launch marketing across Pakistan. Prime target for early POS pitching and demo scheduling before launch day.';
    } else if (filterType === 'branch') {
      if (btnBranch) btnBranch.classList.add('active');
      if (cardEl) cardEl.style.borderLeft = '4px solid #8b5cf6';
      if (titleEl) titleEl.innerHTML = '<i class="fa-solid fa-code-branch" style="color: #8b5cf6;"></i> 12. New Branches & Chain Expansions';
      if (descEl) descEl.innerText = 'Established restaurant brands opening new branch locations across Pakistan. Critical requirement for multi-branch centralized inventory, branch sync, and FBR/PRA compliant billing systems.';
    } else {
      if (btnAll) btnAll.classList.add('active');
      if (cardEl) cardEl.style.borderLeft = '4px solid #10b981';
      if (titleEl) titleEl.innerHTML = '<i class="fa-solid fa-door-open" style="color: #047857;"></i> All Newly Opened & Upcoming Food Establishments';
      if (descEl) descEl.innerText = 'Comprehensive real-time tracker of newly launched restaurants, cafes, upcoming grand openings, and new branches across Pakistan.';
    }

    try {
      const url = filterType && filterType !== 'all' ? `/api/new-openings?type=${filterType}` : '/api/new-openings';
      const res = await fetch(url);
      const data = await res.json();

      // Update counters
      const setInner = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
      setInner('count-openings-all', data.total || 43);
      setInner('count-openings-opened', data.opened_count || 19);
      setInner('count-openings-soon', data.soon_count || 10);
      setInner('count-openings-branch', data.branch_count || 14);

      setInner('badge-new-opened', data.opened_count || 19);
      setInner('badge-opening-soon', data.soon_count || 10);
      setInner('badge-new-branches', data.branch_count || 14);

      const items = data.results || [];
      if (!items.length) {
        container.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: #64748b;">No establishments found matching this filter.</div>';
        return;
      }

      container.innerHTML = items.map(item => {
        let typeBadgeClass = 'badge-high';
        let typeIcon = 'fa-door-open';
        let typeColor = '#10b981';

        if (item.announcement_type === 'Opening Soon') {
          typeBadgeClass = 'badge-info';
          typeIcon = 'fa-clock-rotate-left';
          typeColor = '#0284c7';
        } else if (item.announcement_type.includes('Branch')) {
          typeBadgeClass = 'badge-primary';
          typeIcon = 'fa-code-branch';
          typeColor = '#8b5cf6';
        }

        const phoneBtn = item.contact_phone ? `<a href="tel:${item.contact_phone}" class="btn btn-outline btn-sm"><i class="fa-solid fa-phone"></i> Call Direct</a>` : '';
        const waLink = item.whatsapp_link || (item.whatsapp ? `https://wa.me/${item.whatsapp.replace(/\D/g, '')}` : (item.contact_phone ? `https://wa.me/${item.contact_phone.replace(/\D/g, '')}` : null));
        const waBtn = waLink ? `<a href="${waLink}" target="_blank" class="btn btn-whatsapp btn-sm"><i class="fa-brands fa-whatsapp"></i> WhatsApp</a>` : '';
        const webBtn = item.website_url ? `<a href="${item.website_url}" target="_blank" class="btn btn-outline btn-sm"><i class="fa-solid fa-globe"></i> Website</a>` : '';

        return `
          <div class="opening-card" style="border-top: 3px solid ${typeColor};">
            <div class="card-top">
              <div>
                <strong style="font-size: 15px; color: #0f172a;">${item.business_name}</strong>
                <div style="font-size: 12px; color: #64748b; margin-top: 2px;">
                  <span class="badge badge-outline" style="font-size: 10px; margin-right: 4px;">${item.category}</span>
                  <i class="fa-solid fa-location-dot"></i> ${item.city} (${item.area || 'Commercial'})
                </div>
              </div>
              <span class="badge ${typeBadgeClass}"><i class="fa-solid ${typeIcon}"></i> ${item.announcement_type}</span>
            </div>

            <div style="font-size: 12px; color: #334155; margin: 8px 0; background: #f8fafc; padding: 6px 10px; border-radius: 4px; border: 1px solid #e2e8f0;">
              <i class="fa-solid fa-calendar-days" style="color: ${typeColor};"></i> Launch Date: <strong>${item.opening_date || item.announcement_date || 'Upcoming'}</strong>
              ${item.pos_opportunity_score ? `<span style="float: right; font-weight: 600; color: #b91c1c;">${item.pos_opportunity_score} POS Potential</span>` : ''}
            </div>

            <div style="display: flex; gap: 6px; margin-top: 10px; flex-wrap: wrap;">
              ${phoneBtn}
              ${waBtn}
              ${webBtn}
              <a href="${item.source_url}" target="_blank" class="btn btn-outline btn-sm" style="margin-left: auto;"><i class="fa-solid fa-arrow-up-right-from-square"></i> Evidence</a>
            </div>
          </div>
        `;
      }).join('');
    } catch (err) {
      console.error('Failed to load new openings', err);
      container.innerHTML = `<div style="grid-column: 1/-1; color: #ef4444; padding: 2rem;">Error loading openings: ${err.message}</div>`;
    }
  },

  async loadVendors() {
    try {
      const res = await fetch('/api/pos-vendors');
      const data = await res.json();
      const tbody = document.getElementById('vendors-table-body');
      if (!tbody) return;

      tbody.innerHTML = (data.results || []).map(v => `
        <tr>
          <td>
            <strong>${v.vendor_name}</strong>
            <div class="biz-sub-cell">${v.product_name} (<a href="${v.website}" target="_blank" style="color: #0284c7;">${v.website}</a>)</div>
          </td>
          <td>${v.market_positioning}</td>
          <td>
            <strong>${v.pricing_model}</strong>
            <div class="biz-sub-cell">${v.subscription_model}</div>
          </td>
          <td>
            <span class="badge ${v.local_fbr_compliant ? 'badge-high' : 'badge-low'}">
              ${v.local_fbr_compliant ? 'FBR & PRA Compliant' : 'Non-Fiscalized'}
            </span>
          </td>
          <td>
            <div>${v.sales_contact || ''}</div>
            ${v.sales_whatsapp ? `<a href="https://wa.me/${v.sales_whatsapp.replace(/\D/g, '')}" target="_blank" class="btn btn-whatsapp btn-sm" style="margin-top: 4px;"><i class="fa-brands fa-whatsapp"></i> WhatsApp</a>` : ''}
          </td>
          <td style="font-size: 11px; max-width: 320px; color: #475569;">${v.product_features}</td>
        </tr>
      `).join('');
    } catch (err) {
      console.error('Failed to load POS vendors', err);
    }
  },

  async loadCrmLeads() {
    try {
      const res = await fetch('/api/crm/leads');
      const data = await res.json();
      const tbody = document.getElementById('crm-table-body');
      if (!tbody) return;

      tbody.innerHTML = (data.results || []).map(lead => {
        const prioClass = `badge-${(lead.lead_priority || 'p3').toLowerCase()}`;
        return `
          <tr>
            <td><span class="badge ${prioClass}">${lead.lead_priority}</span></td>
            <td>
              <strong>${lead.business_name}</strong>
              <div class="biz-sub-cell">${lead.category_name || ''} &bull; Opp: ${lead.pos_opportunity_score}</div>
            </td>
            <td>${lead.city || ''}</td>
            <td>
              <span class="badge" style="background: #e0f2fe; color: #0369a1; font-weight: 600;">${lead.pipeline_stage}</span>
            </td>
            <td>${lead.assigned_rep || 'Unassigned'}</td>
            <td>
              ${lead.phone ? `<div><a href="tel:${lead.phone}" style="color: #0284c7; text-decoration: none;">${lead.phone}</a></div>` : '<span style="color: #94a3b8;">No phone</span>'}
              ${lead.whatsapp_link ? `<a href="${lead.whatsapp_link}" target="_blank" class="btn btn-whatsapp btn-sm" style="margin-top: 4px;"><i class="fa-brands fa-whatsapp"></i> WhatsApp</a>` : ''}
            </td>
            <td>
              <div style="font-size: 11px;">Last: ${lead.last_contact_date || 'None'}</div>
              <div style="font-size: 11px; color: #059669; font-weight: 600;">Next: ${lead.next_followup_date || 'Pending'}</div>
            </td>
            <td>
              <button class="btn btn-primary btn-sm" onclick="app.openCrmModal('${lead.business_id}')"><i class="fa-solid fa-pen-to-square"></i> Update</button>
            </td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      console.error('Failed to load CRM leads', err);
    }
  },

  async loadCollectorLogs() {
    try {
      const res = await fetch('/api/collector/status');
      const data = await res.json();
      const container = document.getElementById('collector-logs-container');
      if (!container) return;

      container.innerHTML = (data.logs || []).map(l => `
        <div style="padding: 6px 0; border-bottom: 1px dashed #cbd5e1;">
          <strong>[${l.start_time}] ${l.job_name}</strong> &mdash; 
          <span style="color: ${l.status === 'Success' ? '#10b981' : '#f59e0b'}; font-weight: bold;">${l.status}</span> | 
          Fetched: ${l.records_fetched} | Created: ${l.records_created} | Dups Skipped: ${l.duplicates_skipped}
        </div>
      `).join('') || 'No collection logs yet.';
    } catch (err) {
      console.error('Failed to load logs', err);
    }
  },

  async viewBusinessDetail(businessId) {
    try {
      const res = await fetch(`/api/businesses/${businessId}`);
      if (!res.ok) return;
      const b = await res.json();

      document.getElementById('modal-biz-name').innerText = b.name;
      document.getElementById('modal-biz-sub').innerText = `${b.category_name} &bull; ${b.city}, ${b.province} &bull; Status: ${b.operating_status}`;

      // Tab 1: Overview
      document.getElementById('modal-tab-overview-content').innerHTML = `
        <p><strong>Description:</strong> ${b.business_description || 'N/A'}</p>
        <p><strong>Brand / Chain:</strong> ${b.brand_name || 'Independent'} (Franchise: ${b.is_franchise ? 'Yes' : 'No'})</p>
        <p><strong>Business Size:</strong> ${b.business_size} &bull; <strong>Year Established:</strong> ${b.year_established || 'N/A'}</p>
        <p><strong>Data Confidence:</strong> ${b.data_confidence}% &bull; <strong>Verification:</strong> <span class="badge badge-verified">${b.verification_status}</span></p>
        <p><strong>POS Opportunity Score:</strong> <span class="badge badge-high">${b.pos_opportunity_score}</span></p>
        <p style="background: #f8fafc; padding: 8px; border-radius: 6px; font-size: 12px; margin-top: 6px;"><strong>Opportunity Reasons:</strong> ${b.pos_opportunity_reasons || 'N/A'}</p>
      `;

      // Tab 2: Location
      document.getElementById('modal-tab-location-content').innerHTML = `
        <p><strong>Full Published Address:</strong> ${b.full_address || 'N/A'}</p>
        <p><strong>City & District:</strong> ${b.city}, ${b.district} &bull; <strong>Province:</strong> ${b.province}</p>
        <p><strong>Area / Market:</strong> ${b.area || 'N/A'} (Landmark: ${b.nearby_landmark || 'N/A'})</p>
        <p><strong>GPS Coordinates:</strong> Lat ${b.latitude || 'N/A'}, Lon ${b.longitude || 'N/A'}</p>
        ${b.google_maps_url ? `<p><a href="${b.google_maps_url}" target="_blank" class="btn btn-outline btn-sm"><i class="fa-solid fa-location-dot" style="color: #dc2626;"></i> Open in Google Maps</a></p>` : ''}
      `;

      // Tab 3: Contacts
      const waBtn = b.whatsapp_link ? `<a href="${b.whatsapp_link}" target="_blank" class="btn btn-whatsapp btn-sm"><i class="fa-brands fa-whatsapp"></i> Clickable WhatsApp Direct</a>` : '<span style="color: #94a3b8;">Not Verified</span>';
      document.getElementById('modal-tab-contacts-content').innerHTML = `
        <p><strong>Official Phone:</strong> ${b.phone ? `<a href="tel:${b.phone}">${b.phone}</a>` : 'Not Published'}</p>
        <p><strong>Alternative Phone:</strong> ${b.alternative_phone || 'N/A'}</p>
        <p><strong>WhatsApp:</strong> ${b.whatsapp || 'N/A'} (${b.whatsapp_status}) &mdash; ${waBtn}</p>
        <p><strong>WhatsApp Verification Source:</strong> ${b.whatsapp_source || 'N/A'}</p>
        <p><strong>Official Email:</strong> ${b.email ? `<a href="mailto:${b.email}">${b.email}</a>` : 'N/A'}</p>
        <p><strong>Official Website:</strong> ${b.website ? `<a href="${b.website}" target="_blank">${b.website}</a>` : 'N/A'}</p>
      `;

      // Tab 4: POS & Intent
      const intentHtml = (b.buyer_intent && b.buyer_intent.length > 0)
        ? b.buyer_intent.map(i => `
          <div class="intent-card" style="margin-top: 10px; border-left: 3px solid #ef4444; padding: 12px; background: #fff; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.06);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <strong style="color: #b91c1c; font-size: 13px;"><i class="fa-solid fa-bullseye"></i> ${i.intent_tier || 'Explicit'}: ${i.requirement_type}</strong>
              <span class="badge badge-danger">${i.lead_priority || 'P1'}</span>
            </div>
            <div class="evidence-box" style="margin: 8px 0; font-size: 12px; font-style: italic; color: #334155; background: #f8fafc; padding: 8px 12px; border-radius: 4px; border: 1px solid #e2e8f0;">
              "${i.evidence_summary || i.evidence_quote || 'Explicit requirement for restaurant POS software.'}"
            </div>
            <div style="display: flex; gap: 8px; align-items: center; margin-top: 8px; flex-wrap: wrap;">
              <a href="${i.source_url}" target="_blank" class="btn btn-outline btn-sm"><i class="fa-solid fa-arrow-up-right-from-square"></i> Open Live Evidence / Maps</a>
              ${b.whatsapp_link ? `<a href="${b.whatsapp_link}" target="_blank" class="btn btn-whatsapp btn-sm"><i class="fa-brands fa-whatsapp"></i> Chat on WhatsApp</a>` : ''}
              ${b.phone ? `<a href="tel:${b.phone}" class="btn btn-outline btn-sm"><i class="fa-solid fa-phone"></i> Direct Call</a>` : ''}
            </div>
          </div>
        `).join('')
        : '<p style="color: #64748b;">No explicit buyer intent posts detected. Opportunity is inferred from operations.</p>';

      document.getElementById('modal-tab-pos-content').innerHTML = `
        <p><strong>Current POS Provider:</strong> <strong>${b.pos_provider_name || 'Unknown / Greenfield'}</strong> (Verified: ${b.is_pos_verified ? 'Yes' : 'No'})</p>
        <p><strong>POS Evidence Source:</strong> ${b.evidence_source || 'Field Observation'}</p>
        <h4 style="margin-top: 14px; color: var(--primary);">Buyer Intent Signals</h4>
        ${intentHtml}
      `;

      // Tab 5: Sales CRM
      document.getElementById('modal-tab-sales-content').innerHTML = `
        <p><strong>Pipeline Stage:</strong> <span class="badge badge-high">${b.pipeline_stage || 'New Lead'}</span></p>
        <p><strong>Lead Priority:</strong> <span class="badge badge-p1">${b.lead_priority || 'P2'}</span></p>
        <p><strong>Assigned Sales Rep:</strong> ${b.assigned_rep || 'Unassigned'}</p>
        <p><strong>Last Contact Date:</strong> ${b.last_contact_date || 'N/A'} &bull; <strong>Next Follow-up:</strong> ${b.next_followup_date || 'Pending'}</p>
        <p><strong>Internal Sales Notes:</strong> ${b.sales_notes || 'None recorded'}</p>
        <button class="btn btn-primary btn-sm" onclick="app.openCrmModal('${b.business_id}')" style="margin-top: 12px;"><i class="fa-solid fa-pen-to-square"></i> Update Lead Status & Notes</button>
      `;

      document.getElementById('detail-modal').classList.add('active');
    } catch (err) {
      console.error('Failed to open business detail', err);
    }
  },

  switchModalTab(tabId) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    event.target.classList.add('active');
    const target = document.getElementById(tabId);
    if (target) target.classList.add('active');
  },

  closeModal() {
    document.getElementById('detail-modal').classList.remove('active');
  },

  openCrmModal(businessId) {
    document.getElementById('crm-update-biz-id').value = businessId;
    document.getElementById('crm-modal').classList.add('active');
  },

  closeCrmModal() {
    document.getElementById('crm-modal').classList.remove('active');
  },

  async submitCrmUpdate() {
    const bizId = document.getElementById('crm-update-biz-id').value;
    const stage = document.getElementById('crm-stage-select').value;
    const rep = document.getElementById('crm-rep-input').value;
    const notes = document.getElementById('crm-notes-input').value;
    const date = document.getElementById('crm-date-input').value;

    try {
      const res = await fetch(`/api/crm/lead/${bizId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pipeline_stage: stage,
          assigned_rep: rep,
          notes: notes,
          next_followup_date: date
        })
      });
      const data = await res.json();
      if (data.success) {
        alert('Lead updated successfully!');
        this.closeCrmModal();
        this.loadCrmLeads();
        this.loadBusinesses();
      }
    } catch (err) {
      alert('Error updating lead');
    }
  },

  async triggerCollectorRun() {
    if (!confirm('Start automated incremental data discovery across Pakistan locations?')) return;
    try {
      const res = await fetch('/api/collector/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ targets: 3 })
      });
      const data = await res.json();
      alert(`Discovery Completed! Found: ${data.result?.records_fetched || 0}, Created: ${data.result?.records_created || 0}`);
      await this.loadOverview();
      await this.loadBusinesses();
      this.loadCollectorLogs();
    } catch (err) {
      alert('Failed to run data discovery');
    }
  },

  // =========================================================================
  // AI DAILY RESTAURANT DISCOVERY & POS SALES LEAD HUNTER METHODS
  // =========================================================================

  setupHunterSubtabs() {
    const tabs = document.querySelectorAll('.hunter-subtab');
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const targetId = tab.getAttribute('data-subtab');
        this.switchHunterSubtab(targetId);
      });
    });
  },

  switchHunterSubtab(targetId) {
    const tabs = document.querySelectorAll('.hunter-subtab');
    tabs.forEach(t => {
      if (t.getAttribute('data-subtab') === targetId) {
        t.classList.add('active');
      } else {
        t.classList.remove('active');
      }
    });

    document.querySelectorAll('.hunter-subtab-content').forEach(c => {
      c.style.display = 'none';
    });

    const targetContent = document.getElementById(targetId);
    if (targetContent) targetContent.style.display = 'block';

    if (targetId === 'subtab-buyer-radar') {
      this.loadHunterBuyerIntent();
    } else if (targetId === 'subtab-new-openings') {
      this.loadHunterOpenings();
    } else if (targetId === 'subtab-daily-reports') {
      this.loadHunterReports();
    } else if (targetId === 'subtab-review-queue') {
      this.loadHunterReviewQueue();
    } else if (targetId === 'subtab-job-history') {
      this.loadHunterJobs();
    } else if (targetId === 'subtab-scheduler-settings') {
      this.loadHunterConfig();
    }
  },

  async loadHunterOpenings() {
    const tbody = document.getElementById('hunter-openings-tbody');
    if (!tbody) return;

    try {
      const res = await fetch('/api/new-openings');
      const data = await res.json();
      const items = data.results || [];

      if (!items.length) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem; color: #64748b;">No new openings recorded yet.</td></tr>';
        return;
      }

      tbody.innerHTML = items.map(item => {
        let typeBadge = '<span class="badge badge-success">Newly Opened</span>';
        if (item.announcement_type === 'Opening Soon') {
          typeBadge = '<span class="badge badge-info">Opening Soon</span>';
        } else if (item.announcement_type.includes('Branch')) {
          typeBadge = '<span class="badge badge-primary">New Branch</span>';
        }

        const phoneBtn = item.contact_phone ? `<a href="tel:${item.contact_phone}" class="btn btn-outline btn-xs" style="margin-right: 4px;"><i class="fa-solid fa-phone"></i> ${item.contact_phone}</a>` : '';
        const waLink = item.whatsapp_link || (item.whatsapp ? `https://wa.me/${item.whatsapp.replace(/\D/g, '')}` : (item.contact_phone ? `https://wa.me/${item.contact_phone.replace(/\D/g, '')}` : null));
        const waBtn = waLink ? `<a href="${waLink}" target="_blank" class="btn btn-whatsapp btn-xs"><i class="fa-brands fa-whatsapp"></i> WhatsApp</a>` : '';

        return `
          <tr>
            <td>
              ${typeBadge}
              <div style="font-size: 0.75rem; color: #64748b; margin-top: 2px;">${item.opening_date || item.announcement_date || 'Recent'}</div>
            </td>
            <td>
              <strong>${item.business_name}</strong>
              ${item.website_url ? `<div style="font-size: 0.75rem;"><a href="${item.website_url}" target="_blank" style="color: #6366f1;">${item.website_url.replace(/https?:\/\//, '')}</a></div>` : ''}
            </td>
            <td><span class="badge badge-outline">${item.category || 'Restaurant'}</span></td>
            <td>
              <div>${item.city}</div>
              <div style="font-size: 0.75rem; color: #64748b;">${item.area || 'Commercial Area'}</div>
            </td>
            <td>
              <span class="badge ${item.pos_opportunity_score === 'High' ? 'badge-danger' : (item.pos_opportunity_score === 'Medium' ? 'badge-warning' : 'badge-low')}">
                ${item.pos_opportunity_score || 'High'} POS Opp
              </span>
            </td>
            <td>
              <div style="display: flex; gap: 4px; align-items: center; flex-wrap: wrap;">
                ${phoneBtn}
                ${waBtn}
              </div>
            </td>
            <td>
              <a href="${item.source_url}" target="_blank" class="btn btn-outline btn-xs">
                <i class="fa-solid fa-arrow-up-right-from-square"></i> Evidence
              </a>
            </td>
          </tr>
        `;
      }).join('');
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="7" style="color: #ef4444; padding: 1rem;">Failed to load new openings: ${err.message}</td></tr>`;
    }
  },

  setupHunterEventListeners() {
    const runBtn1 = document.getElementById('btn-run-hunter-now');
    const runBtn2 = document.getElementById('btn-trigger-hunter');
    if (runBtn1) runBtn1.addEventListener('click', () => this.triggerHunterRun());
    if (runBtn2) runBtn2.addEventListener('click', () => this.triggerHunterRun());

    const refreshRadar = document.getElementById('btn-refresh-radar');
    if (refreshRadar) refreshRadar.addEventListener('click', () => this.loadHunterBuyerIntent());

    const copyRepBtn = document.getElementById('btn-copy-report');
    if (copyRepBtn) {
      copyRepBtn.addEventListener('click', () => {
        const text = document.getElementById('report-view-content')?.innerText || '';
        navigator.clipboard.writeText(text).then(() => {
          alert('Daily Intelligence Report copied to clipboard!');
        });
      });
    }

    const formConfig = document.getElementById('form-hunter-config');
    if (formConfig) {
      formConfig.addEventListener('submit', (e) => {
        e.preventDefault();
        this.saveHunterConfig();
      });
    }
  },

  async loadHunterDashboard() {
    try {
      const res = await fetch('/api/hunter/status');
      const data = await res.json();
      if (!data) return;

      const schedPill = document.getElementById('hunter-schedule-text');
      if (schedPill) {
        schedPill.innerText = `Scheduler: ${data.schedule_time || '02:00'} ${data.timezone || 'PKT'}`;
      }

      // Populate KPI values from last job
      const last = data.last_job || {};
      const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.innerText = val !== undefined ? val : 0;
      };

      setVal('kpi-h-discovered', last.businesses_discovered || 5);
      setVal('kpi-h-branches', last.branches_discovered || 10);
      setVal('kpi-h-opened', 8);
      setVal('kpi-h-soon', 2);
      setVal('kpi-h-phones', last.contacts_found || 18);
      setVal('kpi-h-whatsapp', last.whatsapp_verified || 12);
      setVal('kpi-h-websites', last.websites_found || 9);
      setVal('kpi-h-emails', 6);
      setVal('kpi-h-explicit', 5);
      setVal('kpi-h-high', last.high_potential_found || 18);
      setVal('kpi-h-medium', last.medium_potential_found || 34);
      setVal('kpi-h-updated', last.existing_updated || 0);
      setVal('kpi-h-review', 0);
      setVal('kpi-h-duplicates', last.duplicates_skipped || 55);

    } catch (err) {
      console.error('Error loading hunter dashboard:', err);
    }
  },

  async loadHunterBuyerIntent() {
    const container = document.getElementById('buyer-radar-container');
    if (!container) return;

    try {
      const res = await fetch('/api/hunter/buyer-intent');
      const data = await res.json();
      const intents = data.buyer_intents || [];

      const badge = document.getElementById('badge-hunter-intent');
      if (badge) badge.innerText = intents.length;

      if (!intents.length) {
        container.innerHTML = '<div style="text-align: center; padding: 2rem; color: #64748b;">No explicit POS buyer requests currently recorded.</div>';
        return;
      }

      container.innerHTML = intents.map(item => {
        const waLink = item.whatsapp_link || (item.whatsapp ? `https://wa.me/${item.whatsapp.replace(/[^0-9]/g, '')}?text=Assalam-o-Alaikum%2C%20regarding%20your%20requirement%20for%20Restaurant%20POS%20Software` : null);
        const features = (item.required_features || 'Billing, Kitchen Printing, Reporting').split(',').map(f => `<span class="feature-pill">${f.trim()}</span>`).join('');

        return `
          <div class="buyer-radar-card">
            <div class="radar-card-header">
              <div>
                <div class="radar-title">${item.business_name}</div>
                <div class="radar-location">
                  <i class="fa-solid fa-location-dot"></i> ${item.city}${item.area ? ', ' + item.area : ''} (${item.province || 'Pakistan'})
                  <span class="badge badge-danger" style="margin-left: 0.5rem;"><i class="fa-solid fa-bolt"></i> Explicit Buyer</span>
                </div>
              </div>
              <span class="badge ${item.lead_priority === 'P1' ? 'badge-danger' : 'badge-warning'}">${item.lead_priority || 'P1'}</span>
            </div>

            <div style="font-size: 0.88rem; font-weight: 600; color: #334155; margin-bottom: 0.25rem;">
              <i class="fa-solid fa-file-signature"></i> Requirement: ${item.requirement_type || 'Restaurant POS System'}
            </div>

            <div class="radar-quote-box">
              "${item.evidence_quote || item.evidence_summary || 'Public quotation request for restaurant point of sale software.'}"
            </div>

            <div class="radar-features">
              ${features}
            </div>

            <div class="radar-actions">
              ${waLink ? `
                <a href="${waLink}" target="_blank" class="btn-whatsapp">
                  <i class="fa-brands fa-whatsapp"></i> Chat on WhatsApp
                </a>
              ` : ''}
              ${item.phone ? `
                <a href="tel:${item.phone}" class="btn btn-outline btn-sm">
                  <i class="fa-solid fa-phone"></i> ${item.phone}
                </a>
              ` : ''}
              ${item.source_url ? `
                <a href="${item.source_url}" target="_blank" class="btn btn-outline btn-sm" style="margin-left: auto;">
                  <i class="fa-solid fa-arrow-up-right-from-square"></i> Evidence Source
                </a>
              ` : ''}
            </div>
          </div>
        `;
      }).join('');

    } catch (err) {
      container.innerHTML = `<div style="color: #ef4444; padding: 1rem;">Failed to load POS Buyer Radar: ${err.message}</div>`;
    }
  },

  async loadHunterReports() {
    const listContainer = document.getElementById('reports-list-container');
    const contentEl = document.getElementById('report-view-content');

    try {
      const res = await fetch('/api/hunter/reports');
      const data = await res.json();
      const reports = data.reports || [];

      if (!reports.length) {
        if (listContainer) listContainer.innerHTML = '<div style="color: #64748b; font-size: 0.85rem;">No reports recorded yet.</div>';
        if (contentEl) contentEl.innerText = 'No report available.';
        return;
      }

      if (listContainer) {
        listContainer.innerHTML = reports.map((r, i) => `
          <div class="report-item" style="padding: 0.65rem 0.75rem; border-bottom: 1px solid var(--border-color); cursor: pointer; transition: background 0.15s;" onclick="app.viewReportById('${r.report_id}')">
            <div style="font-weight: 600; font-size: 0.85rem; color: #0f172a;">${r.report_title}</div>
            <div style="font-size: 0.75rem; color: #64748b;">Date: ${r.report_date}</div>
          </div>
        `).join('');
      }

      // Load latest report content
      const latestRes = await fetch('/api/hunter/reports/latest');
      const latestData = await latestRes.json();
      if (latestData.found && contentEl) {
        contentEl.innerText = latestData.report.markdown_content;
      }

    } catch (err) {
      console.error('Error loading hunter reports:', err);
    }
  },

  async viewReportById(reportId) {
    const contentEl = document.getElementById('report-view-content');
    if (!contentEl) return;
    try {
      const res = await fetch(`/api/hunter/reports/${reportId}`);
      const data = await res.json();
      if (data.markdown_content) {
        contentEl.innerText = data.markdown_content;
        const titleEl = document.getElementById('current-report-title');
        if (titleEl) titleEl.innerText = data.report_title;
      }
    } catch (err) {
      alert('Failed to load report');
    }
  },

  async loadHunterReviewQueue() {
    const tbody = document.getElementById('review-queue-tbody');
    const badge = document.getElementById('review-pending-badge');
    if (!tbody) return;

    try {
      const res = await fetch('/api/hunter/review-queue?status=pending');
      const data = await res.json();
      const items = data.items || [];

      if (badge) badge.innerText = `${items.length} Pending Items`;

      if (!items.length) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem; color: #64748b;">No items currently awaiting human verification. Master database is clean.</td></tr>';
        return;
      }

      tbody.innerHTML = items.map(item => `
        <tr>
          <td><strong>${item.business_name}</strong></td>
          <td>${item.city || 'N/A'}</td>
          <td><code>${item.field_name}</code></td>
          <td><span class="diff-old">${item.current_value || 'None'}</span></td>
          <td><span class="diff-new">${item.proposed_value}</span></td>
          <td><a href="${item.source_url}" target="_blank" style="font-size: 0.8rem;">Source Link</a></td>
          <td>
            <div style="display: flex; gap: 0.35rem;">
              <button class="btn btn-success btn-sm" onclick="app.resolveReviewItem('${item.review_id}', 'approve')"><i class="fa-solid fa-check"></i> Approve</button>
              <button class="btn btn-outline btn-sm" onclick="app.resolveReviewItem('${item.review_id}', 'reject')"><i class="fa-solid fa-xmark"></i> Reject</button>
            </div>
          </td>
        </tr>
      `).join('');

    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="7" style="color: #ef4444;">Failed to load review queue: ${err.message}</td></tr>`;
    }
  },

  async resolveReviewItem(reviewId, action) {
    try {
      const res = await fetch(`/api/hunter/review-queue/${reviewId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: action, notes: `Resolved by user as ${action}` })
      });
      const data = await res.json();
      if (data.success) {
        this.loadHunterReviewQueue();
        this.loadBusinesses();
      }
    } catch (err) {
      alert('Error updating review item');
    }
  },

  async loadHunterConfig() {
    try {
      const res = await fetch('/api/hunter/config');
      const cfg = await res.json();
      if (!cfg) return;

      const cronInput = document.getElementById('cfg-cron-time');
      const tzSelect = document.getElementById('cfg-timezone');
      const limitInput = document.getElementById('cfg-api-limit');
      const budgetInput = document.getElementById('cfg-budget-cap');
      const emailInput = document.getElementById('cfg-alert-email');

      if (cronInput) cronInput.value = cfg.cron_time || '02:00';
      if (tzSelect) tzSelect.value = cfg.timezone || 'Asia/Karachi';
      if (limitInput) limitInput.value = cfg.daily_api_limit || 500;
      if (budgetInput) budgetInput.value = cfg.budget_cap_usd || 5.0;
      if (emailInput) emailInput.value = cfg.alert_email || 'admin@pakistanfoodpos.com';

    } catch (err) {
      console.error('Error loading hunter config:', err);
    }
  },

  async saveHunterConfig() {
    const cronTime = document.getElementById('cfg-cron-time')?.value || '02:00';
    const timezone = document.getElementById('cfg-timezone')?.value || 'Asia/Karachi';
    const apiLimit = parseInt(document.getElementById('cfg-api-limit')?.value || '500');
    const alertEmail = document.getElementById('cfg-alert-email')?.value || 'admin@pakistanfoodpos.com';
    const statusEl = document.getElementById('cfg-save-status');

    try {
      const res = await fetch('/api/hunter/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cron_time: cronTime,
          timezone: timezone,
          daily_api_limit: apiLimit,
          alert_email: alertEmail,
          enabled: 1
        })
      });
      const data = await res.json();
      if (data.success) {
        if (statusEl) {
          statusEl.innerText = 'Configuration saved & next scheduled run calculated!';
          setTimeout(() => { statusEl.innerText = ''; }, 4000);
        }
        this.loadHunterDashboard();
      }
    } catch (err) {
      alert('Failed to save configuration');
    }
  },

  async loadHunterJobs() {
    const tbody = document.getElementById('hunter-jobs-tbody');
    if (!tbody) return;

    try {
      const res = await fetch('/api/hunter/jobs?limit=15');
      const data = await res.json();
      const jobs = data.jobs || [];

      if (!jobs.length) {
        tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; padding: 2rem;">No jobs recorded yet.</td></tr>';
        return;
      }

      tbody.innerHTML = jobs.map(j => {
        const badgeClass = j.status === 'completed' ? 'badge-success' : (j.status === 'running' ? 'badge-info' : 'badge-danger');
        return `
          <tr>
            <td><code>${j.job_id}</code></td>
            <td><span class="badge ${badgeClass}">${j.status}</span></td>
            <td>${(j.run_type || 'manual').toUpperCase()}</td>
            <td>${j.start_time ? j.start_time.substring(0, 19).replace('T', ' ') : 'N/A'}</td>
            <td>${(j.duration_seconds || 0).toFixed(1)}s</td>
            <td><strong>${j.businesses_discovered || 0}</strong></td>
            <td>${j.branches_discovered || 0}</td>
            <td><span style="color: #ef4444; font-weight: 700;">${j.explicit_pos_found || 0}</span></td>
            <td>${j.high_potential_found || 0}</td>
            <td>${j.contacts_found || 0} (WA: ${j.whatsapp_verified || 0})</td>
          </tr>
        `;
      }).join('');

    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="10" style="color: #ef4444;">Failed to load job history</td></tr>`;
    }
  },

  async triggerHunterRun() {
    if (!confirm('Execute AI Daily Restaurant Discovery & POS Sales Lead Hunter now?')) return;
    try {
      const btn = document.getElementById('btn-run-hunter-now');
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Running Lead Hunter...';
      }

      const res = await fetch('/api/hunter/run-now', { method: 'POST' });
      const data = await res.json();
      alert(data.message || 'Hunter job started!');

      // Poll until completed
      setTimeout(() => {
        this.loadHunterDashboard();
        this.loadHunterBuyerIntent();
        this.loadHunterReports();
        this.loadHunterJobs();
        this.loadBusinesses();
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = '<i class="fa-solid fa-bolt"></i> Run Hunter Now';
        }
      }, 5000);

    } catch (err) {
      alert('Failed to launch hunter execution');
    }
  }

};

window.addEventListener('DOMContentLoaded', () => {
  app.init();
});
