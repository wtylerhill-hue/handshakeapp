/* Handshake AMH — main.js */

const CSRF = document.querySelector('meta[name="csrf-token"]')?.content ?? '';

// ── 1. Client-side table filter (dashboard) ──
(function initTableFilter() {
  const statusSel   = document.getElementById('filter-status');
  const sourceSel   = document.getElementById('filter-source');
  const fromInput   = document.getElementById('filter-deadline-from');
  const toInput     = document.getElementById('filter-deadline-to');
  const resetBtn    = document.getElementById('filter-reset');
  const rows        = document.querySelectorAll('.app-row');
  if (!statusSel && !sourceSel) return;

  function applyFilters() {
    const status = statusSel?.value ?? '';
    const source = sourceSel?.value ?? '';
    const from   = fromInput?.value  ?? '';
    const to     = toInput?.value    ?? '';

    rows.forEach(row => {
      const rStatus   = row.dataset.status   ?? '';
      const rSource   = row.dataset.source   ?? '';
      const rDeadline = row.dataset.deadline ?? '';

      let show = true;
      if (status && rStatus !== status)  show = false;
      if (source && rSource !== source)  show = false;
      if (from   && rDeadline && rDeadline < from) show = false;
      if (to     && rDeadline && rDeadline > to)   show = false;

      row.style.display = show ? '' : 'none';
    });
  }

  [statusSel, sourceSel, fromInput, toInput].forEach(el => {
    el?.addEventListener('change', applyFilters);
  });

  resetBtn?.addEventListener('click', () => {
    if (statusSel)  statusSel.value  = '';
    if (sourceSel)  sourceSel.value  = '';
    if (fromInput)  fromInput.value  = '';
    if (toInput)    toInput.value    = '';
    rows.forEach(row => { row.style.display = ''; });
  });
})();


// ── 2. Source toggle (application form) ──
(function initSourceToggle() {
  const sourceSelect    = document.getElementById('source');
  const externalGroup   = document.getElementById('external-company-group');
  const postingGroup    = document.getElementById('posting-group');
  if (!sourceSelect) return;

  function toggleSourceFields() {
    const isExternal = sourceSelect.value === 'External';
    if (externalGroup) externalGroup.style.display = isExternal ? '' : 'none';
    if (postingGroup)  postingGroup.style.display  = isExternal ? 'none' : '';
  }

  sourceSelect.addEventListener('change', toggleSourceFields);
  toggleSourceFields();
})();


// ── 3. Notification acknowledge ──
document.querySelectorAll('.notif-ack').forEach(btn => {
  btn.addEventListener('click', () => {
    const id   = btn.dataset.id;
    const item = document.getElementById(`notif-${id}`);
    fetch(`/notifications/${id}/acknowledge`, {
      method: 'POST',
      headers: { 'X-CSRFToken': CSRF }
    }).then(res => {
      if (res.status === 204) item?.remove();
    });
  });
});


// ── 4. Advisor student search ──
(function initAdvisorSearch() {
  const input    = document.getElementById('student-search');
  const dropdown = document.getElementById('student-dropdown');
  const panel    = document.getElementById('student-panel');
  if (!input) return;

  let debounceTimer;

  input.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    const q = input.value.trim();
    if (q.length < 2) { dropdown.style.display = 'none'; return; }

    debounceTimer = setTimeout(() => {
      fetch(`/advisor/search?q=${encodeURIComponent(q)}`)
        .then(r => r.json())
        .then(students => {
          dropdown.innerHTML = '';
          if (!students.length) { dropdown.style.display = 'none'; return; }

          students.forEach(s => {
            const item = document.createElement('div');
            item.className = 'student-dropdown-item';
            item.innerHTML = `
              <strong>${s.First_Name} ${s.Last_Name}</strong>
              <span class="student-dropdown-meta"> — ${s.Email}</span>
              <div class="student-dropdown-meta">${s.Major ?? ''} ${s.Graduation_Year ? '· ' + s.Graduation_Year : ''}</div>
            `;
            item.addEventListener('click', () => {
              input.value = `${s.First_Name} ${s.Last_Name}`;
              dropdown.style.display = 'none';
              loadStudentDetail(s.ProfileID);
            });
            dropdown.appendChild(item);
          });
          dropdown.style.display = 'block';
        });
    }, 250);
  });

  document.addEventListener('click', e => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.style.display = 'none';
    }
  });

  function loadStudentDetail(id) {
    fetch(`/advisor/student/${id}`)
      .then(r => r.json())
      .then(data => renderStudentPanel(data));
  }

  function renderStudentPanel({ student, applications, postings, stats }) {
    if (!panel) return;
    const skills = (student.Skills ?? '').split(',').filter(Boolean)
      .map(s => `<span class="skill-pill">${s.trim()}</span>`).join('');

    panel.innerHTML = `
      <div class="advisor-split">
        <div class="profile-card">
          <div class="profile-name">${student.First_Name} ${student.Last_Name}</div>
          <div class="profile-email">${student.Email}</div>
          <div class="stat-strip" style="grid-template-columns:repeat(2,1fr);margin-bottom:16px;">
            <div class="stat-box"><div class="stat-number">${stats.total}</div><div class="stat-label">Total</div></div>
            <div class="stat-box"><div class="stat-number">${stats.active}</div><div class="stat-label">Active</div></div>
            <div class="stat-box"><div class="stat-number">${stats.interviewing}</div><div class="stat-label">Interviewing</div></div>
            <div class="stat-box"><div class="stat-number">${stats.offered}</div><div class="stat-label">Offers</div></div>
          </div>
          <div class="profile-row"><div class="profile-row-label">Major</div><div>${student.Major ?? '—'}</div></div>
          <div class="profile-row"><div class="profile-row-label">Grad Year</div><div>${student.Graduation_Year ?? '—'}</div></div>
          <div class="profile-row"><div class="profile-row-label">Location Pref</div><div>${student.Location_Preference ?? '—'}</div></div>
          <div class="profile-row"><div class="profile-row-label">Job Type</div><div>${student.Job_Type_Preference ?? '—'}</div></div>
          ${skills ? `<div class="profile-row"><div class="profile-row-label">Skills</div><div>${skills}</div></div>` : ''}
        </div>
        <div>
          <div class="tab-bar">
            <button class="tab-btn active" data-tab="tab-history">Application History</button>
            <button class="tab-btn" data-tab="tab-jobs">Recommended Jobs</button>
          </div>
          <div id="tab-history" class="tab-panel active">${buildAppTable(applications)}</div>
          <div id="tab-jobs" class="tab-panel">${buildJobsTable(postings)}</div>
        </div>
      </div>
    `;

    // Wire up tabs
    panel.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        panel.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        panel.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        panel.querySelector(`#${btn.dataset.tab}`).classList.add('active');
      });
    });
  }

  function buildAppTable(apps) {
    if (!apps.length) return '<p class="table-empty">No applications on record.</p>';
    const rows = apps.map(a => `
      <tr>
        <td>${a.Company_Name}</td>
        <td>${a.Job_Title}</td>
        <td><span class="badge badge-${a.Status.toLowerCase()}">${a.Status}</span></td>
        <td class="mono">${a.Date_Applied ?? '—'}</td>
        <td class="mono">${a.Deadline ?? '—'}</td>
      </tr>`).join('');
    return `<table class="data-table">
      <thead><tr><th>Company</th><th>Role</th><th>Status</th><th>Applied</th><th>Deadline</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
  }

  function buildJobsTable(postings) {
    if (!postings.length) return '<p class="table-empty">No active postings.</p>';
    const rows = postings.map(p => `
      <tr>
        <td>${p.Company_Name}</td>
        <td>${p.Job_Title}</td>
        <td class="mono">${p.Location_Type}</td>
        <td class="mono">${p.Salary_Range}</td>
        <td>
          <div class="match-bar-wrap">
            <div class="match-bar-fill" style="width:${Math.min(p.Match_Score,100)}%"></div>
          </div>
        </td>
      </tr>`).join('');
    return `<table class="data-table">
      <thead><tr><th>Company</th><th>Role</th><th>Type</th><th>Salary</th><th>Match</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
  }
})();


// ── 5. Advisor tab switch (static tabs in templates) ──
document.querySelectorAll('.tab-bar').forEach(bar => {
  bar.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const container = bar.closest('[data-tabs]') ?? bar.parentElement;
      container.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      container.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const target = document.getElementById(btn.dataset.tab);
      if (target) target.classList.add('active');
    });
  });
});


// ── 6. Employer form progress ──
(function initEmployerProgress() {
  const form       = document.getElementById('post-job-form');
  const submitBtn  = document.getElementById('submit-btn');
  const step1Dot   = document.getElementById('step-1');
  const step2Dot   = document.getElementById('step-2');
  if (!form) return;

  const step1Fields = ['company_name','contact_name','contact_email'];
  const step2Fields = ['job_title','description','location_type','salary_range',
                       'required_qualifications','application_deadline'];

  function isFilledAll(names) {
    return names.every(n => (form.elements[n]?.value ?? '').trim().length > 0);
  }

  function updateProgress() {
    const s1 = isFilledAll(step1Fields);
    const s2 = isFilledAll(step2Fields);
    step1Dot?.closest('.progress-step').classList.toggle('done', s1);
    step2Dot?.closest('.progress-step').classList.toggle('done', s2);
    document.getElementById('step-3')?.closest('.progress-step').classList.toggle('done', s1 && s2);
    if (submitBtn) submitBtn.disabled = !(s1 && s2);
  }

  form.addEventListener('input', updateProgress);
  updateProgress();
})();


// ── 7. Document library filter tabs ──
(function initDocTabs() {
  const tabs = document.querySelectorAll('.doc-tab');
  if (!tabs.length) return;

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const filter = tab.dataset.type ?? '';
      document.querySelectorAll('.doc-row').forEach(row => {
        row.style.display = (!filter || row.dataset.type === filter) ? '' : 'none';
      });
    });
  });
})();


// ── 8. Employer status toggle ──
document.querySelectorAll('.toggle-status').forEach(btn => {
  btn.addEventListener('click', () => {
    const id  = btn.dataset.id;
    const row = btn.closest('tr');
    fetch(`/employer/posting/${id}/toggle`, {
      method: 'POST',
      headers: { 'X-CSRFToken': CSRF }
    })
      .then(r => r.json())
      .then(({ status }) => {
        const badge = row.querySelector('.posting-badge');
        if (badge) {
          badge.textContent = status;
          badge.className = `badge badge-${status.toLowerCase()} posting-badge`;
        }
        btn.textContent = status === 'Active' ? 'Close' : 'Reopen';
      });
  });
});


// ── Register field toggle (register form) ──
(function initRegisterToggle() {
  const roleSelect     = document.getElementById('role');
  const studentFields  = document.getElementById('student-fields');
  const advisorFields  = document.getElementById('advisor-fields');
  if (!roleSelect) return;

  function toggleRoleFields() {
    const role = roleSelect.value;
    if (studentFields) studentFields.style.display = role === 'Student' ? '' : 'none';
    if (advisorFields) advisorFields.style.display = role === 'Advisor' ? '' : 'none';
  }

  roleSelect.addEventListener('change', toggleRoleFields);
  toggleRoleFields();
})();
