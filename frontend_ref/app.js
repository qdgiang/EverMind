const icon = (name) => {
  const paths = {
    task: '<path d="M6 4h12v16H6zM9 8h6M9 12h6M9 16h4"/>',
    decision: '<path d="M12 3v18M5 8h14M7 16h10"/>',
    evidence: '<path d="M7 3h10v18H7zM10 8h4M10 12h4M10 16h3"/>',
    link: '<path d="M10 13a4 4 0 0 0 5.7.1l2.2-2.2a4 4 0 0 0-5.7-5.7L11 6.4"/><path d="M14 11a4 4 0 0 0-5.7-.1l-2.2 2.2a4 4 0 0 0 5.7 5.7l1.2-1.2"/>',
    telegram: '<path d="m20 4-3 16-5-5-3 3-1-5-5-2 17-7Z"/><path d="m8 13 8-5"/>',
    transcript: '<path d="M6 4h12v16H6zM9 8h6M9 12h6M9 16h4"/>',
    clock: '<circle cx="12" cy="12" r="8"/><path d="M12 8v5l3 2"/>',
    user: '<circle cx="12" cy="8" r="3"/><path d="M6 20c.5-4 2.5-6 6-6s5.5 2 6 6"/>',
    message: '<path d="M5 5h14v11H9l-4 3V5Z"/>',
    arrow: '<path d="M5 12h14M14 7l5 5-5 5"/>',
    chevron: '<path d="m9 18 6-6-6-6"/>',
    dependency: '<path d="M5 7h7v10h7"/><path d="m16 14 3 3-3 3"/>',
    check: '<path d="m5 12 4 4L19 6"/>',
    more: '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
    close: '<path d="m6 6 12 12M18 6 6 18"/>',
    external: '<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 13v6H5V6h6"/>',
  };
  return `<svg viewBox="0 0 24 24" aria-hidden="true">${paths[name] || paths.task}</svg>`;
};

const people = {
  minh: { name: "Minh", initials: "MN", className: "avatar-minh" },
  linh: { name: "Linh Nguyễn", initials: "LN", className: "avatar-linh" },
  mai: { name: "Mai", initials: "MA", className: "avatar-mai" },
  khoa: { name: "Khoa", initials: "KH", className: "avatar-khoa" },
};

const evidence = {
  m0016: {
    id: "m0016",
    source: "Telegram",
    channel: "aiv-trungthu",
    author: "minh",
    timestamp: "28 Aug · 09:14",
    revision: "rev 1",
    role: "proposes",
    text: "Em đề xuất đặt 200 đèn lồng giấy bên Kim Long, giá đang tốt và kịp giao trước ngày 20/9.",
    highlight: "đặt 200 đèn lồng giấy bên Kim Long",
    context: "Reply thread: Lantern planning · 3 messages before · 2 messages after",
    hash: "sha256:8f4c…a921",
    locator: "telegram:aiv-trungthu:m0016",
    backlinks: ["D-03 · Original lantern order", "T-02 · Lantern order"],
  },
  m0018: {
    id: "m0018",
    source: "Telegram",
    channel: "aiv-trungthu",
    author: "linh",
    timestamp: "28 Aug · 09:21",
    revision: "rev 1",
    role: "approves",
    text: "Ok chốt nhé, Minh triển khai giúp chị.",
    highlight: "Ok chốt nhé",
    context: "Replying to m0016 · Approval authority: coordinator",
    hash: "sha256:93bd…418c",
    locator: "telegram:aiv-trungthu:m0018",
    backlinks: ["D-03 · Original lantern order", "T-02 · Lantern order"],
  },
  m0082: {
    id: "m0082",
    source: "Telegram",
    channel: "aiv-trungthu",
    author: "linh",
    timestamp: "15 Sep · 16:40",
    revision: "rev 1",
    role: "supports",
    text: "Đổi đơn sang 150 đèn LED nhé. Loại giấy có rủi ro cháy khi các bé cầm, an toàn là ưu tiên trước.",
    highlight: "Đổi đơn sang 150 đèn LED",
    context: "Project group · Mentioned task T-02 · Supersedes the earlier order",
    hash: "sha256:c62e…0b37",
    locator: "telegram:aiv-trungthu:m0082",
    backlinks: ["D-10 · Switch to LED lanterns", "T-02 · Lantern order", "Policy · Child safety"],
  },
  m0085: {
    id: "m0085",
    source: "Telegram",
    channel: "aiv-trungthu",
    author: "minh",
    timestamp: "16 Sep · 10:12",
    revision: "rev 1",
    role: "reports",
    text: "!blocked Kim Long chưa xác nhận còn đủ 150 đèn LED, em đang chờ họ phản hồi tồn kho.",
    highlight: "Kim Long chưa xác nhận còn đủ 150 đèn LED",
    context: "Marker capture · Linked deterministically to T-02",
    hash: "sha256:34ea…15d0",
    locator: "telegram:aiv-trungthu:m0085",
    backlinks: ["U-06 · Blocked update", "T-02 · Lantern order", "Party · Kim Long"],
  },
  m0034: {
    id: "m0034",
    source: "Telegram",
    channel: "aiv-trungthu",
    author: "mai",
    timestamp: "02 Sep · 14:05",
    revision: "rev 1",
    role: "supports",
    text: "Nhà văn hóa đã xác nhận giữ sân tối 26/9, mình có thể bắt đầu chốt sơ đồ booth.",
    highlight: "xác nhận giữ sân tối 26/9",
    context: "Venue thread · Linked to T-01 and T-04",
    hash: "sha256:1a3c…7e12",
    locator: "telegram:aiv-trungthu:m0034",
    backlinks: ["D-01 · Confirm venue", "T-01 · Venue confirmation", "T-04 · Booth layout"],
  },
  tr0042: {
    id: "tr-0042",
    source: "Transcript",
    channel: "All-hands 07 Sep",
    author: "khoa",
    timestamp: "07 Sep · [42:18]",
    revision: "rev 1",
    role: "supports",
    text: "Phần âm thanh đã test xong, hai loa chính hoạt động ổn và đội kỹ thuật nhận bàn giao.",
    highlight: "âm thanh đã test xong",
    context: "Meeting transcript · Speaker mapped to @khoa",
    hash: "sha256:6baf…2cc1",
    locator: "transcript:meeting-2026-09-07:42:18",
    backlinks: ["U-03 · Sound test complete", "T-03 · Sound system"],
  },
};

const decisions = {
  "D-01": {
    id: "D-01",
    title: "Confirm community house as venue",
    summary: "Reserve the community house courtyard for the charity night.",
    status: "effective",
    date: "02 Sep",
    maker: "Mai",
    taskIds: ["T-01", "T-04"],
    evidenceIds: ["m0034"],
    facet: "attr:venue",
  },
  "D-03": {
    id: "D-03",
    title: "Order 200 paper lanterns",
    summary: "Initial order from Kim Long, approved by Linh.",
    status: "superseded",
    date: "28 Aug",
    maker: "Linh Nguyễn",
    taskIds: ["T-02"],
    evidenceIds: ["m0016", "m0018"],
    facet: "attr:order",
    supersededBy: "D-10",
  },
  "D-04": {
    id: "D-04",
    title: "Rent two main speakers",
    summary: "Use the verified sound package for the main stage.",
    status: "effective",
    date: "04 Sep",
    maker: "Khoa",
    taskIds: ["T-03"],
    evidenceIds: ["tr0042"],
    facet: "attr:equipment",
  },
  "D-07": {
    id: "D-07",
    title: "Move education booth near main gate",
    summary: "Improve visibility and simplify the visitor flow.",
    status: "effective",
    date: "10 Sep",
    maker: "Mai",
    taskIds: ["T-04"],
    evidenceIds: ["m0034"],
    facet: "attr:layout",
  },
  "D-10": {
    id: "D-10",
    title: "Switch to 150 LED lanterns",
    summary: "Replace paper lanterns with LED units for child safety.",
    status: "effective",
    date: "15 Sep",
    maker: "Linh Nguyễn",
    taskIds: ["T-02", "T-05"],
    evidenceIds: ["m0082"],
    facet: "attr:order",
    supersedes: "D-03",
  },
  "D-11": {
    id: "D-11",
    title: "Add fire-safety checkpoints",
    summary: "Place checks at the stage, entrance and activity zone.",
    status: "proposed",
    date: "17 Sep",
    maker: "Minh",
    taskIds: ["T-05"],
    evidenceIds: ["m0082"],
    facet: "attr:safety-checkpoints",
  },
};

const tasks = [
  {
    id: "T-01",
    title: "Venue confirmation",
    status: "doing",
    owner: "mai",
    due: "18 Sep",
    decisionIds: ["D-01"],
    evidenceIds: ["m0034"],
    dependencies: [],
    summary: "Community house courtyard is reserved; written confirmation is still being collected.",
    facts: { Venue: "Nhà văn hóa", Owner: "Mai", Deadline: "18 Sep", Team: "Events" },
  },
  {
    id: "T-02",
    title: "Lantern order",
    status: "blocked",
    owner: "minh",
    due: "20 Sep",
    decisionIds: ["D-10", "D-03"],
    evidenceIds: ["m0082", "m0085", "m0016", "m0018"],
    dependencies: [{ taskId: "T-01", type: "needs confirmed venue" }],
    summary: "Current order is 150 LED lanterns. Waiting for Kim Long to confirm inventory.",
    facts: { Order: "150 LED", Owner: "Minh", Deadline: "20 Sep", "Waiting on": "Kim Long" },
  },
  {
    id: "T-03",
    title: "Sound system",
    status: "done",
    owner: "khoa",
    due: "16 Sep",
    decisionIds: ["D-04"],
    evidenceIds: ["tr0042"],
    dependencies: [],
    summary: "Two main speakers have passed the sound check and were handed to the technical team.",
    facts: { Equipment: "2 main speakers", Owner: "Khoa", Completed: "16 Sep", Team: "Events" },
  },
  {
    id: "T-04",
    title: "Booth layout",
    status: "doing",
    owner: "mai",
    due: "21 Sep",
    decisionIds: ["D-07", "D-01"],
    evidenceIds: ["m0034"],
    dependencies: [{ taskId: "T-01", type: "blocked by venue" }],
    summary: "Layout draft uses the confirmed courtyard, with the education booth beside the main gate.",
    facts: { Layout: "Draft v2", Owner: "Mai", Deadline: "21 Sep", Booths: "8" },
  },
  {
    id: "T-05",
    title: "Child safety plan",
    status: "doing",
    owner: "minh",
    due: "22 Sep",
    decisionIds: ["D-11", "D-10"],
    evidenceIds: ["m0082"],
    dependencies: [{ taskId: "T-02", type: "depends on lantern type" }],
    summary: "Safety plan reflects the LED change; three additional checkpoints are awaiting approval.",
    facts: { Checkpoints: "3 proposed", Owner: "Minh", Deadline: "22 Sep", Risk: "Low" },
  },
  {
    id: "T-06",
    title: "Volunteer roster",
    status: "doing",
    owner: "khoa",
    due: "23 Sep",
    decisionIds: [],
    evidenceIds: [],
    dependencies: [{ taskId: "T-04", type: "needs booth count" }],
    summary: "Twenty-six of thirty volunteer slots are filled; assignment depends on the final booth layout.",
    facts: { Filled: "26 / 30", Owner: "Khoa", Deadline: "23 Sep", Missing: "4" },
  },
];

const projectMembers = [
  { id: "linh", role: "Project coordinator", responsibility: "Final authority · cross-team decisions" },
  { id: "mai", role: "Events team lead", responsibility: "Venue, layout and event operations" },
  { id: "minh", role: "Logistics PIC", responsibility: "Lantern vendor and child-safety work" },
  { id: "khoa", role: "Technical & volunteer PIC", responsibility: "Sound system and volunteer roster" },
];

const knowledgeDocs = [
  {
    id: "project-home",
    group: "Project",
    title: "Project overview",
    shortTitle: "Overview",
    description: "Purpose, scope, operating picture and the people behind the project.",
    updated: "2 min ago",
    author: "linh",
    tags: ["campaign", "active"],
    kind: "home",
    relatedTasks: ["T-01", "T-02", "T-04"],
    relatedDecisions: ["D-10", "D-07"],
    evidenceIds: ["m0082", "m0034"],
    backlinks: ["project-brief", "operations", "child-safety", "meeting-sep-07"],
  },
  {
    id: "project-brief",
    group: "Core documents",
    title: "Project brief & scope",
    shortTitle: "Project brief",
    description: "What the campaign is trying to achieve, what is in scope and what success means.",
    updated: "12 Sep",
    author: "linh",
    tags: ["brief", "scope"],
    lead: "A one-night charity campaign for children, designed to bring programs, volunteers and local partners into one coordinated event.",
    sections: [
      { title: "Purpose", paragraphs: ["Create a safe Mid-Autumn experience for local children while raising visibility and support for AIV's ongoing Weekend Classes program."] },
      { title: "Scope", bullets: ["One charity night at the community house on 26 September", "Eight activity and education booths", "Main-stage program, lantern activity and volunteer operations", "Vendor, venue and ward-office coordination"] },
      { title: "Success signals", bullets: ["All safety-critical tasks completed before event day", "Thirty confirmed volunteers", "No unresolved external blocker at T−48h", "Reusable operating notes captured for the next campaign"] },
    ],
    relatedTasks: ["T-01", "T-04", "T-06"],
    relatedDecisions: ["D-01", "D-07"],
    evidenceIds: ["m0034"],
    backlinks: ["project-home", "operations", "meeting-sep-07"],
  },
  {
    id: "operations",
    group: "Core documents",
    title: "Venue & operations plan",
    shortTitle: "Venue & operations",
    description: "Venue facts, booth layout, access constraints and operating dependencies.",
    updated: "15 Sep",
    author: "mai",
    tags: ["operations", "venue"],
    lead: "The community-house courtyard is the operating base. The layout is now grounded on the confirmed venue and keeps the education booth near the main gate.",
    sections: [
      { title: "Confirmed facts", bullets: ["Venue: Phương Liệt community house courtyard", "Event window: 17:00–21:00, 26 September", "Eight booths plus one main-stage zone", "Technical setup begins at 13:30"] },
      { title: "Dependencies", paragraphs: ["The booth layout depends on written venue confirmation. Volunteer placement then depends on the final booth count and access map."] },
      { title: "Open items", bullets: ["Collect signed venue confirmation", "Confirm emergency access lane", "Publish final booth map to team leads"] },
    ],
    relatedTasks: ["T-01", "T-04", "T-06"],
    relatedDecisions: ["D-01", "D-07"],
    evidenceIds: ["m0034"],
    backlinks: ["project-home", "project-brief", "child-safety"],
  },
  {
    id: "child-safety",
    group: "Notes",
    title: "Child-safety policy",
    shortTitle: "Child safety",
    description: "Safety rules that shape purchasing, layout and event-day operations.",
    updated: "15 Sep",
    author: "linh",
    tags: ["policy", "safety"],
    lead: "Child safety overrides cost or visual preference. Any item handled directly by children must be low-heat, non-flammable and supervised.",
    sections: [
      { title: "Current policy", bullets: ["Use LED lanterns instead of paper lanterns with candles", "Keep all power and sound cables outside child pathways", "Maintain three safety checkpoints: entrance, activity zone and main stage"] },
      { title: "Why this changed", paragraphs: ["The initial paper-lantern order was superseded after the coordinator identified a fire risk. The current order is 150 LED lanterns."] },
      { title: "Application", paragraphs: ["This policy currently shapes the lantern order and the child-safety plan. Future task decisions should link back here when they touch materials, electricity or crowd flow."] },
    ],
    relatedTasks: ["T-02", "T-05"],
    relatedDecisions: ["D-10", "D-11", "D-03"],
    evidenceIds: ["m0082", "m0085"],
    backlinks: ["project-home", "operations", "vendor-kim-long"],
  },
  {
    id: "vendor-kim-long",
    group: "Notes",
    title: "Vendor note · Kim Long",
    shortTitle: "Vendor · Kim Long",
    description: "Relationship history, current order and unresolved vendor dependency.",
    updated: "16 Sep",
    author: "minh",
    tags: ["party", "vendor", "blocked"],
    lead: "Kim Long is the selected lantern vendor. The relationship is active, but inventory confirmation for 150 LED units remains unresolved.",
    sections: [
      { title: "Current engagement", bullets: ["Requested quantity: 150 LED lanterns", "Required delivery: before 20 September", "Current state: waiting for inventory confirmation", "Relationship owner: Minh"] },
      { title: "History", paragraphs: ["The first request was for 200 paper lanterns. After the safety decision, Minh asked Kim Long to change the order to LED units."] },
      { title: "Next action", paragraphs: ["Escalate to the Events lead if Kim Long does not confirm stock by the end of 17 September."] },
    ],
    relatedTasks: ["T-02"],
    relatedDecisions: ["D-10", "D-03"],
    evidenceIds: ["m0016", "m0085"],
    backlinks: ["child-safety", "meeting-sep-07"],
  },
  {
    id: "meeting-sep-07",
    group: "Notes",
    title: "All-hands notes · 07 Sep",
    shortTitle: "All-hands · 07 Sep",
    description: "Decisions, progress and follow-ups captured from the project meeting.",
    updated: "07 Sep",
    author: "khoa",
    tags: ["meeting", "transcript"],
    lead: "The meeting aligned venue, sound and volunteer operations. The source transcript remains linked at the turn level.",
    sections: [
      { title: "Highlights", bullets: ["Sound package passed the initial test", "Venue layout can proceed after written confirmation", "Volunteer roster target remains thirty people"] },
      { title: "Follow-ups", bullets: ["Khoa to hand over sound equipment to the technical team", "Mai to close the venue confirmation", "Team leads to nominate missing volunteer slots"] },
    ],
    relatedTasks: ["T-01", "T-03", "T-06"],
    relatedDecisions: ["D-01", "D-04"],
    evidenceIds: ["tr0042", "m0034"],
    backlinks: ["project-home", "project-brief", "vendor-kim-long"],
  },
];

const state = {
  selectedTaskId: "T-02",
  selectedDecisionId: "D-10",
  selectedDocId: "project-home",
  currentView: "knowledge",
  inspectorMode: null,
  showInactive: true,
};

const els = {
  viewPanel: document.getElementById("viewPanel"),
  inspector: document.getElementById("inspector"),
  searchOverlay: document.getElementById("searchOverlay"),
  searchInput: document.getElementById("globalSearch"),
  searchResults: document.getElementById("searchResults"),
  evidenceModal: document.getElementById("evidenceModal"),
  modalContent: document.getElementById("modalContent"),
  toast: document.getElementById("toast"),
  sidebar: document.getElementById("sidebar"),
  sidebarScrim: document.getElementById("sidebarScrim"),
};

const avatarMarkup = (personId) => {
  const person = people[personId] || people.minh;
  return `<span class="mini-avatar ${person.className}" title="${person.name}">${person.initials}</span>`;
};

const statusLabel = (status) => ({ doing: "In progress", blocked: "Blocked", done: "Done" })[status] || status;

function renderKnowledgeView() {
  const doc = knowledgeDocs.find((item) => item.id === state.selectedDocId) || knowledgeDocs[0];
  const groups = [...new Set(knowledgeDocs.map((item) => item.group))];

  els.viewPanel.innerHTML = `
    <div class="kb-shell">
      <nav class="kb-doc-nav" aria-label="Project knowledge documents">
        <div class="kb-nav-head">
          <div>
            <span>Knowledge base</span>
            <strong>Đêm hội Trăng Rằm</strong>
          </div>
          <button class="icon-button" aria-label="Thêm tài liệu">+</button>
        </div>
        <label class="kb-nav-search" for="kbDocFilter">${icon("evidence")}<input id="kbDocFilter" type="search" placeholder="Search inside files…" autocomplete="off" /><kbd>/</kbd></label>
        <div class="kb-nav-scroll">
          ${groups.map((group) => `
            <section class="kb-nav-group">
              <h3>${group}</h3>
              ${knowledgeDocs.filter((item) => item.group === group).map((item) => `
                <button class="kb-doc-link ${item.id === doc.id ? "active" : ""}" data-doc-id="${item.id}">
                  <span class="kb-doc-icon">${icon(item.kind === "home" ? "link" : item.tags.includes("meeting") ? "message" : "evidence")}</span>
                  <span><strong>${item.shortTitle}</strong><small>${item.updated}</small></span>
                  ${item.tags.includes("blocked") ? '<i class="kb-alert-dot"></i>' : ""}
                </button>`).join("")}
            </section>`).join("")}
          <section class="kb-nav-group kb-collections">
            <h3>Linked collections</h3>
            <button class="kb-collection-link" data-view-switch="map">${icon("task")}<span>Tasks</span><strong>10</strong></button>
            <button class="kb-collection-link" data-view-switch="decisions">${icon("decision")}<span>Decisions</span><strong>8</strong></button>
            <button class="kb-collection-link" data-view-switch="evidence">${icon("evidence")}<span>Evidence</span><strong>24</strong></button>
          </section>
        </div>
      </nav>

      <article class="kb-article">
        ${renderKnowledgeArticle(doc)}
      </article>

      <aside class="kb-context" aria-label="Project context and backlinks">
        ${renderKnowledgeContext(doc)}
      </aside>
    </div>`;
}

function renderKnowledgeArticle(doc) {
  const author = people[doc.author] || people.linh;
  return `
    <header class="kb-article-head">
      <div class="kb-article-kicker"><span>${doc.group}</span><span>·</span><span>Last updated ${doc.updated}</span></div>
      <h2>${doc.title}</h2>
      <p>${doc.description}</p>
      <div class="kb-byline">
        <span class="avatar ${author.className}">${author.initials}</span>
        <span><strong>${author.name}</strong><small>Owner of this page</small></span>
        <div class="kb-tags">${doc.tags.map((tag) => `<span>${tag}</span>`).join("")}</div>
      </div>
    </header>
    ${doc.kind === "home" ? renderProjectHome(doc) : renderDocumentBody(doc)}
  `;
}

function renderProjectHome(doc) {
  const featuredDocs = knowledgeDocs.filter((item) => item.id !== "project-home").slice(0, 4);
  return `
    <div class="kb-article-body">
      <section class="kb-hero-note">
        <div class="kb-hero-icon">月</div>
        <div>
          <span class="section-kicker">Project summary</span>
          <p>A one-night charity campaign for children that coordinates venue, logistics, safety, volunteers and local partners—while leaving behind reusable organizational memory.</p>
        </div>
      </section>

      <section class="kb-property-grid" aria-label="Project properties">
        <div><span>Status</span><strong><i class="property-dot active"></i>Active campaign</strong></div>
        <div><span>Event date</span><strong>26 Sep 2026</strong></div>
        <div><span>Lead team</span><strong>Events team</strong></div>
        <div><span>Coordinator</span><strong>Linh Nguyễn</strong></div>
        <div><span>Location</span><strong>Phương Liệt community house</strong></div>
        <div><span>Knowledge health</span><strong><i class="property-dot healthy"></i>24 receipts linked</strong></div>
      </section>

      <section class="kb-content-section">
        <div class="kb-section-title"><div><span>01</span><h3>About this project</h3></div><button data-doc-id="project-brief">Open full brief →</button></div>
        <p>Đêm hội Trăng Rằm connects AIV's volunteers, Weekend Classes program and local partners in a community charity night. The project runs as a dated campaign: planning and task state close after the event, while decisions, evidence and lessons remain searchable.</p>
        <p>The current operating model is decision-driven. Material changes—venue, order quantity, assignments and safety policy—are captured as decisions. Day-to-day execution remains in lightweight task updates.</p>
        <div class="kb-inline-links">
          <button data-open-task="T-02">${icon("task")}T-02 · Lantern order</button>
          <button data-open-decision="D-10">${icon("decision")}D-10 · Switch to LED</button>
          <button data-evidence-id="m0082">${icon("evidence")}Receipt m0082</button>
        </div>
      </section>

      <section class="kb-content-section">
        <div class="kb-section-title"><div><span>02</span><h3>Current operating picture</h3></div><button data-view-switch="map">Open task panels →</button></div>
        <div class="kb-situation-grid">
          <button class="kb-situation-card" data-open-task="T-01">
            <span class="situation-status doing"><i></i>In progress</span>
            <strong>Venue confirmation</strong>
            <p>Courtyard reserved; collecting signed confirmation.</p>
            <small>T-01 · Mai · due 18 Sep</small>
          </button>
          <button class="kb-situation-card blocked" data-open-task="T-02">
            <span class="situation-status blocked"><i></i>Needs action</span>
            <strong>Lantern inventory</strong>
            <p>Waiting on Kim Long to confirm 150 LED units.</p>
            <small>T-02 · Minh · blocked 1 day</small>
          </button>
          <button class="kb-situation-card" data-open-task="T-04">
            <span class="situation-status doing"><i></i>In progress</span>
            <strong>Booth layout</strong>
            <p>Draft v2 uses the confirmed courtyard plan.</p>
            <small>T-04 · Mai · due 21 Sep</small>
          </button>
        </div>
      </section>

      <section class="kb-content-section">
        <div class="kb-section-title"><div><span>03</span><h3>Key knowledge documents</h3></div><small>${knowledgeDocs.length - 1} documents</small></div>
        <div class="kb-document-grid">
          ${featuredDocs.map((item) => `
            <button class="kb-document-card" data-doc-id="${item.id}">
              <span class="kb-document-type">${item.group}</span>
              <strong>${item.title}</strong>
              <p>${item.description}</p>
              <span class="kb-document-meta">Updated ${item.updated}${icon("chevron")}</span>
            </button>`).join("")}
        </div>
      </section>

      <section class="kb-content-section kb-milestones">
        <div class="kb-section-title"><div><span>04</span><h3>Project milestones</h3></div><small>Event time</small></div>
        <div class="milestone-row done"><time>02 Sep</time><i></i><div><strong>Venue selected</strong><small>Community-house courtyard reserved</small></div></div>
        <div class="milestone-row done"><time>15 Sep</time><i></i><div><strong>Safety-driven order change</strong><small>LED lantern decision became effective</small></div></div>
        <div class="milestone-row current"><time>20 Sep</time><i></i><div><strong>Operations locked</strong><small>Vendor, layout and volunteer roster due</small></div></div>
        <div class="milestone-row"><time>26 Sep</time><i></i><div><strong>Event day</strong><small>Đêm hội Trăng Rằm</small></div></div>
      </section>
    </div>`;
}

function renderDocumentBody(doc) {
  const firstEvidence = doc.evidenceIds.map((id) => evidence[id]).find(Boolean);
  return `
    <div class="kb-article-body">
      <section class="kb-lead-copy"><p>${doc.lead}</p></section>
      ${doc.sections.map((section, index) => `
        <section class="kb-content-section kb-prose-section">
          <div class="kb-section-title"><div><span>${String(index + 1).padStart(2, "0")}</span><h3>${section.title}</h3></div></div>
          ${(section.paragraphs || []).map((paragraph) => `<p>${paragraph}</p>`).join("")}
          ${section.bullets ? `<ul>${section.bullets.map((item) => `<li>${item}</li>`).join("")}</ul>` : ""}
        </section>`).join("")}
      ${firstEvidence ? `
        <section class="kb-source-callout" data-evidence-id="${firstEvidence.id}">
          <div>${icon(firstEvidence.source === "Transcript" ? "transcript" : "telegram")}<span><strong>Source excerpt · ${firstEvidence.id}</strong><small>${firstEvidence.source} · ${firstEvidence.timestamp}</small></span></div>
          <blockquote>“${firstEvidence.text}”</blockquote>
          <button>Open pinned receipt →</button>
        </section>` : ""}
      <section class="kb-content-section">
        <div class="kb-section-title"><div><span>↗</span><h3>Referenced records</h3></div><small>Typed links</small></div>
        <div class="kb-reference-list">
          ${doc.relatedTasks.map((id) => {
            const task = tasks.find((item) => item.id === id);
            return task ? `<button data-open-task="${id}">${icon("task")}<span><strong>${id} · ${task.title}</strong><small>${statusLabel(task.status)} · ${task.decisionIds.length} decisions</small></span>${icon("chevron")}</button>` : "";
          }).join("")}
          ${doc.relatedDecisions.map((id) => {
            const decision = decisions[id];
            return decision ? `<button data-open-decision="${id}">${icon("decision")}<span><strong>${id} · ${decision.title}</strong><small>${decision.status} · ${decision.date}</small></span>${icon("chevron")}</button>` : "";
          }).join("")}
        </div>
      </section>
    </div>`;
}

function renderKnowledgeContext(doc) {
  return `
    <section class="kb-context-section">
      <div class="kb-context-heading"><h3>Project members</h3><span>${projectMembers.length}</span></div>
      <div class="kb-member-list">
        ${projectMembers.map((member) => {
          const person = people[member.id];
          return `<button class="kb-member-row"><span class="avatar ${person.className}">${person.initials}</span><span><strong>${person.name}</strong><small>${member.role}</small><em>${member.responsibility}</em></span></button>`;
        }).join("")}
      </div>
    </section>

    <section class="kb-context-section">
      <div class="kb-context-heading"><h3>Related tasks</h3><button data-view-switch="map">View all</button></div>
      <div class="kb-related-list">
        ${doc.relatedTasks.slice(0, 4).map((id) => {
          const task = tasks.find((item) => item.id === id);
          return task ? `<button data-open-task="${id}"><i class="related-state ${task.status}"></i><span><strong>${id} · ${task.title}</strong><small>${statusLabel(task.status)} · ${people[task.owner].name}</small></span>${icon("chevron")}</button>` : "";
        }).join("")}
      </div>
    </section>

    <section class="kb-context-section">
      <div class="kb-context-heading"><h3>Related decisions</h3><button data-view-switch="decisions">View log</button></div>
      <div class="kb-related-list decision-links">
        ${doc.relatedDecisions.slice(0, 4).map((id) => {
          const decision = decisions[id];
          return decision ? `<button data-open-decision="${id}">${icon("decision")}<span><strong>${id} · ${decision.title}</strong><small>${decision.status} · ${decision.date}</small></span></button>` : "";
        }).join("")}
      </div>
    </section>

    <section class="kb-context-section backlinks-section">
      <div class="kb-context-heading"><h3>Backlinks</h3><span>${doc.backlinks.length}</span></div>
      <p>Pages that reference this knowledge.</p>
      <div class="kb-backlink-list">
        ${doc.backlinks.map((id) => {
          const linked = knowledgeDocs.find((item) => item.id === id);
          return linked ? `<button data-doc-id="${id}">${icon("link")}<span><strong>${linked.shortTitle}</strong><small>${linked.group}</small></span></button>` : "";
        }).join("")}
      </div>
    </section>`;
}

function renderMap() {
  els.viewPanel.innerHTML = `
    <div class="panel-header">
      <div class="panel-title-group">
        <h2>Project knowledge graph</h2>
        <p>Chọn một task để mở decisions và receipts liên quan</p>
      </div>
      <div class="legend" aria-label="Chú thích">
        <span><i></i> Active</span>
        <span class="legend-blocked"><i></i> Blocked</span>
        <span class="legend-dependency"><i></i> Dependency</span>
      </div>
    </div>
    <div class="knowledge-canvas">
      <div class="project-root">
        <div class="root-icon">月</div>
        <div class="root-copy">
          <span class="node-kicker">Project</span>
          <strong>Đêm hội Trăng Rằm</strong>
          <small>Campaign · Events team · 26 Sep</small>
        </div>
        <div class="root-stats"><strong>10</strong><small>tasks</small></div>
      </div>
      <div class="root-connector"></div>
      <div class="task-network">
        ${tasks.map(renderTaskNode).join("")}
      </div>
      <div class="canvas-footer">
        <span>${icon("dependency")} Dependency là graph edge, không phải cây thư mục</span>
        <button data-view-switch="tasks">Xem tất cả 10 tasks →</button>
      </div>
    </div>`;
}

function renderTaskNode(task) {
  const selected = task.id === state.selectedTaskId ? "selected" : "";
  const dependency = task.dependencies[0];
  return `
    <article class="task-node ${task.status} ${selected}" data-task-id="${task.id}" tabindex="0" role="button" aria-label="Mở ${task.id} ${task.title}">
      <div class="task-node-top">
        <span class="task-id">${task.id}</span>
        <span class="task-state ${task.status}"><i></i>${statusLabel(task.status)}</span>
      </div>
      <h3>${task.title}</h3>
      <div class="task-meta-row">
        <div class="mini-avatars">${avatarMarkup(task.owner)}</div>
        <span>Due ${task.due}</span>
      </div>
      <div class="task-node-footer">
        <span class="decision-count">${icon("decision")}${task.decisionIds.length} decision${task.decisionIds.length === 1 ? "" : "s"}</span>
        ${dependency
          ? `<span class="dependency-chip" title="Depends on ${dependency.taskId}: ${dependency.type}">${icon("dependency")}${dependency.taskId}</span>`
          : '<span class="no-dependency">No dependency</span>'}
      </div>
    </article>`;
}

function renderInspector() {
  if (state.inspectorMode === "decision" && decisions[state.selectedDecisionId]) {
    renderDecisionInspector(decisions[state.selectedDecisionId]);
    return;
  }
  renderTaskInspector();
}

function renderTaskInspector() {
  const task = tasks.find((item) => item.id === state.selectedTaskId) || tasks[0];
  const taskDecisions = task.decisionIds.map((id) => decisions[id]).filter(Boolean);
  const visibleDecisions = state.showInactive ? taskDecisions : taskDecisions.filter((decision) => decision.status !== "superseded");
  const taskEvidence = task.evidenceIds.map((id) => evidence[id]).filter(Boolean).slice(0, 3);

  els.inspector.innerHTML = `
    <div class="inspector-head">
      <div class="inspector-head-top">
        <span class="inspector-task-id">${task.id} · Task</span>
        <div class="inspector-actions">
          <button class="icon-button" aria-label="Sao chép link" data-copy-task>${icon("link")}</button>
          <button class="icon-button" aria-label="Thêm tùy chọn">${icon("more")}</button>
        </div>
      </div>
      <h2>${task.title}</h2>
      <div class="inspector-status-row">
        <span class="status-badge ${task.status}"><i></i>${statusLabel(task.status)}</span>
        <span class="source-badge">Events team</span>
        <span class="source-badge">${people[task.owner].name}</span>
      </div>
    </div>
    <div class="inspector-body">
      <div class="current-state-card">
        <div class="section-kicker">
          Current state
          <span class="verified-label">${icon("check")} grounded</span>
        </div>
        <p>${task.summary}</p>
        <div class="state-facts">
          ${Object.entries(task.facts).map(([label, value]) => `<div class="state-fact"><span>${label}</span><strong>${value}</strong></div>`).join("")}
        </div>
      </div>

      <section class="inspector-section">
        <div class="section-heading-row">
          <h3>Dependencies</h3>
          <small>${task.dependencies.length} linked task${task.dependencies.length === 1 ? "" : "s"}</small>
        </div>
        <div class="dependency-list">
          ${task.dependencies.length ? task.dependencies.map((dep) => renderDependency(dep, task)).join("") : '<div class="dependency-item"><div class="dependency-direction">✓</div><div class="dependency-copy"><strong>No blocking dependency</strong><small>This task can progress independently</small></div></div>'}
        </div>
      </section>

      <section class="inspector-section">
        <div class="section-heading-row">
          <h3>Decision lineage</h3>
          <label class="toggle-label">
            Show inactive
            <input id="showInactive" type="checkbox" ${state.showInactive ? "checked" : ""} />
            <span class="toggle"></span>
          </label>
        </div>
        <div class="decision-timeline">
          ${visibleDecisions.length ? visibleDecisions.map(renderDecisionCard).join("") : '<div class="decision-card"><p>No decision records yet. Progress can still exist as task updates.</p></div>'}
        </div>
      </section>

      <section class="inspector-section">
        <div class="section-heading-row">
          <h3>Evidence receipts</h3>
          <small>${task.evidenceIds.length} receipts</small>
        </div>
        <div class="receipt-list">
          ${taskEvidence.length ? taskEvidence.map(renderReceiptCard).join("") : '<div class="receipt-card"><div class="receipt-copy"><strong>No receipts linked yet</strong><p>This task currently exists without extracted decisions.</p></div></div>'}
        </div>
      </section>
    </div>`;
}

function renderDecisionInspector(decision) {
  const statusText = decision.status.charAt(0).toUpperCase() + decision.status.slice(1);
  const decisionEvidence = decision.evidenceIds.map((id) => evidence[id]).filter(Boolean);
  const relation = decision.supersedes
    ? { label: "Supersedes", id: decision.supersedes }
    : decision.supersededBy
      ? { label: "Superseded by", id: decision.supersededBy }
      : null;

  els.inspector.innerHTML = `
    <div class="inspector-head decision-inspector-head">
      <div class="inspector-head-top">
        <span class="inspector-task-id">${decision.id} · Decision</span>
        <div class="inspector-actions">
          <button class="icon-button" aria-label="Copy decision link" data-copy-decision>${icon("link")}</button>
          <button class="icon-button" aria-label="Close decision details" data-close-decision>${icon("close")}</button>
        </div>
      </div>
      <h2>${decision.title}</h2>
      <div class="inspector-status-row">
        <span class="decision-status ${decision.status}"><i></i>${statusText}</span>
        <span class="source-badge">${decision.facet}</span>
        <span class="source-badge">${decision.taskIds.length} affected task${decision.taskIds.length === 1 ? "" : "s"}</span>
      </div>
    </div>
    <div class="inspector-body">
      <div class="current-state-card decision-outcome-card">
        <div class="section-kicker">
          Decision outcome
          <span class="verified-label">${icon("check")} authority checked</span>
        </div>
        <p>${decision.summary}</p>
        <div class="state-facts">
          <div class="state-fact"><span>Status</span><strong>${statusText}</strong></div>
          <div class="state-fact"><span>Scope</span><strong>${decision.taskIds.length > 1 ? "Multiple tasks" : "Task"}</strong></div>
          <div class="state-fact"><span>Facet</span><strong>${decision.facet}</strong></div>
          <div class="state-fact"><span>Event time</span><strong>${decision.date}</strong></div>
          <div class="state-fact"><span>Maker</span><strong>${decision.maker}</strong></div>
          <div class="state-fact"><span>Receipts</span><strong>${decisionEvidence.length} pinned</strong></div>
        </div>
      </div>

      ${relation ? `
        <section class="inspector-section">
          <div class="section-heading-row"><h3>Decision relationship</h3><small>Append-only lineage</small></div>
          <button class="decision-relation-card" data-decision-id="${relation.id}">
            <span>${icon("decision")}</span>
            <span><small>${relation.label}</small><strong>${relation.id} · ${decisions[relation.id]?.title || "Related decision"}</strong></span>
            ${icon("chevron")}
          </button>
        </section>` : ""}

      <section class="inspector-section">
        <div class="section-heading-row"><h3>Affected tasks</h3><small>${decision.taskIds.length} linked</small></div>
        <div class="decision-task-list">
          ${decision.taskIds.map((id) => {
            const task = tasks.find((item) => item.id === id);
            return task ? `<button data-task-id="${id}"><i class="related-state ${task.status}"></i><span><strong>${id} · ${task.title}</strong><small>${statusLabel(task.status)} · ${people[task.owner].name}</small></span>${icon("chevron")}</button>` : "";
          }).join("")}
        </div>
      </section>

      <section class="inspector-section">
        <div class="section-heading-row"><h3>Rationale & context</h3><small>Grounded summary</small></div>
        <div class="decision-rationale"><p>${decision.summary}</p><span>Generated only from the decision record and its cited evidence.</span></div>
      </section>

      <section class="inspector-section">
        <div class="section-heading-row"><h3>Evidence receipts</h3><small>${decisionEvidence.length} pinned</small></div>
        <div class="receipt-list">
          ${decisionEvidence.length ? decisionEvidence.map(renderReceiptCard).join("") : '<div class="receipt-card"><div class="receipt-copy"><strong>No evidence linked</strong><p>This decision has no receipt in the demo data.</p></div></div>'}
        </div>
      </section>
    </div>`;
}

function renderDependency(dependency, currentTask) {
  const linked = tasks.find((item) => item.id === dependency.taskId);
  if (!linked) return "";
  return `
    <button class="dependency-item" data-task-id="${linked.id}">
      <span class="dependency-direction">${icon("dependency")}</span>
      <span class="dependency-copy">
        <strong>${linked.id} · ${linked.title}</strong>
        <small>${dependency.type}</small>
      </span>
      <span class="dependency-state ${linked.status}" title="${statusLabel(linked.status)}"></span>
    </button>`;
}

function renderDecisionCard(decision) {
  const statusText = decision.status.charAt(0).toUpperCase() + decision.status.slice(1);
  const relation = decision.supersedes
    ? `Supersedes ${decision.supersedes}`
    : decision.supersededBy
      ? `Replaced by ${decision.supersededBy}`
      : decision.facet;
  return `
    <article class="decision-card ${decision.status === "superseded" ? "inactive" : ""}" data-decision-id="${decision.id}" tabindex="0" role="button">
      <div class="decision-card-top">
        <span class="decision-card-id">${decision.id}</span>
        <span class="decision-status ${decision.status}"><i></i>${statusText}</span>
      </div>
      <h4>${decision.title}</h4>
      <p>${relation}</p>
      <div class="decision-card-meta">
        <span>${icon("user")}${decision.maker}</span>
        <span>${icon("clock")}${decision.date}</span>
        <span>${icon("evidence")}${decision.evidenceIds.length}</span>
      </div>
    </article>`;
}

function renderReceiptCard(item) {
  const sourceClass = item.source === "Transcript" ? "transcript" : "";
  return `
    <button class="receipt-card" data-evidence-id="${item.id}">
      <span class="receipt-source ${sourceClass}">${icon(item.source === "Transcript" ? "transcript" : "telegram")}</span>
      <span class="receipt-copy">
        <strong><span>${item.id} · ${item.source}</span><span>${item.timestamp}</span></strong>
        <p>“${item.text}”</p>
        <span class="receipt-role">${item.role}</span>
      </span>
    </button>`;
}

function renderTasksView() {
  els.viewPanel.innerHTML = `
    <div class="list-view">
      <div class="list-view-header">
        <div><h2>Project tasks</h2><p>Task state is projected from effective decisions and accepted updates</p></div>
        <div class="filter-chips"><button class="filter-chip active">All 10</button><button class="filter-chip">Active 6</button><button class="filter-chip">Blocked 2</button></div>
      </div>
      <div class="list-cards">
        ${tasks.map((task) => `
          <article class="wide-card task-table-card" data-task-id="${task.id}">
            <span class="task-id">${task.id}</span>
            <span class="wide-card-title"><strong>${task.title}</strong><small>${task.dependencies.length ? `Depends on ${task.dependencies.map((d) => d.taskId).join(", ")}` : "Independent task"}</small></span>
            <span class="status-badge ${task.status} task-list-status"><i></i>${statusLabel(task.status)}</span>
            <span class="task-assignee">${avatarMarkup(task.owner)}${people[task.owner].name}</span>
            <span class="wide-card-context">${task.decisionIds.length} decisions · ${task.evidenceIds.length} receipts</span>
            <span class="wide-card-arrow">${icon("chevron")}</span>
          </article>`).join("")}
      </div>
    </div>`;
}

function renderDecisionsView() {
  const allDecisions = Object.values(decisions);
  els.viewPanel.innerHTML = `
    <div class="list-view">
      <div class="list-view-header">
        <div><h2>Decision log</h2><p>Append-only history with authority, supersession and receipts</p></div>
        <div class="filter-chips"><button class="filter-chip active">All</button><button class="filter-chip">Effective</button><button class="filter-chip">Proposed</button><button class="filter-chip">Inactive</button></div>
      </div>
      <div class="list-cards">
        ${allDecisions.map((decision) => `
          <article class="wide-card" data-decision-id="${decision.id}">
            <span class="decision-card-id">${decision.id}</span>
            <span class="wide-card-title"><strong>${decision.title}</strong><small>${decision.taskIds.join(" · ")} · ${decision.facet}</small></span>
            <span class="wide-card-context">${decision.summary}</span>
            <span class="decision-status ${decision.status}"><i></i>${decision.status}</span>
            <span class="wide-card-arrow">${icon("chevron")}</span>
          </article>`).join("")}
      </div>
    </div>`;
}

function renderEvidenceView() {
  const allEvidence = Object.values(evidence);
  els.viewPanel.innerHTML = `
    <div class="list-view">
      <div class="list-view-header">
        <div><h2>Evidence archive</h2><p>Immutable source revisions with typed backlinks</p></div>
        <div class="filter-chips"><button class="filter-chip active">All sources</button><button class="filter-chip">Telegram</button><button class="filter-chip">Transcripts</button></div>
      </div>
      <div class="evidence-grid">
        ${allEvidence.map((item) => `
          <article class="evidence-tile" data-evidence-id="${item.id}">
            <div class="evidence-tile-top">
              <span class="evidence-tile-source">${icon(item.source === "Transcript" ? "transcript" : "telegram")}${item.id} · ${item.source}</span>
              <span class="revision-badge">${item.revision}</span>
            </div>
            <blockquote>“${item.text}”</blockquote>
            <div class="evidence-tile-bottom">
              <span>${people[item.author]?.name || item.author} · ${item.timestamp}</span>
              <span class="evidence-links">${item.backlinks.slice(0, 2).map((link) => `<span class="evidence-link-chip">${link.split(" · ")[0]}</span>`).join("")}</span>
            </div>
          </article>`).join("")}
      </div>
    </div>`;
}

function syncWorkspaceLayout() {
  const grid = document.getElementById("workspaceGrid");
  const knowledgeMode = state.currentView === "knowledge";
  const showInspector = ["map", "tasks"].includes(state.currentView)
    || (state.currentView === "decisions" && state.inspectorMode === "decision");
  grid.classList.toggle("knowledge-mode", knowledgeMode);
  grid.classList.toggle("full-width-mode", !knowledgeMode && !showInspector);
  return showInspector;
}

function setView(view) {
  state.currentView = view;
  state.inspectorMode = ["map", "tasks"].includes(view) ? "task" : null;
  document.querySelectorAll(".view-tab").forEach((tab) => {
    const active = tab.dataset.view === view;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", String(active));
  });
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.view === view);
  });
  if (view === "knowledge") renderKnowledgeView();
  if (view === "map") renderMap();
  if (view === "tasks") renderTasksView();
  if (view === "decisions") renderDecisionsView();
  if (view === "evidence") renderEvidenceView();
  const showInspector = syncWorkspaceLayout();
  if (!showInspector) {
    els.inspector.innerHTML = "";
  } else {
    renderInspector();
  }
}

function selectTask(taskId) {
  if (!tasks.some((task) => task.id === taskId)) return;
  if (!["map", "tasks"].includes(state.currentView)) setView("map");
  state.selectedTaskId = taskId;
  state.inspectorMode = "task";
  syncWorkspaceLayout();
  if (state.currentView === "map") renderMap();
  renderInspector();
  if (window.innerWidth <= 930) {
    els.inspector.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function openDecision(decisionId) {
  const decision = decisions[decisionId];
  if (!decision) return;
  state.selectedDecisionId = decisionId;
  state.inspectorMode = "decision";
  syncWorkspaceLayout();
  renderInspector();
  if (window.innerWidth <= 930) {
    els.inspector.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function closeDecisionInspector() {
  if (state.currentView === "decisions") {
    state.inspectorMode = null;
    syncWorkspaceLayout();
    els.inspector.innerHTML = "";
    return;
  }
  state.inspectorMode = "task";
  syncWorkspaceLayout();
  renderInspector();
}

function openEvidence(evidenceId, focusedDecisionId = null) {
  const item = evidence[evidenceId];
  if (!item) return;
  const person = people[item.author] || { name: item.author, initials: "?", className: "avatar-bot" };
  const proof = item.text.replace(item.highlight, `<mark class="highlight-proof">${item.highlight}</mark>`);
  const backlinks = focusedDecisionId
    ? [item.backlinks.find((link) => link.startsWith(focusedDecisionId)), ...item.backlinks].filter(Boolean)
    : item.backlinks;
  const uniqueBacklinks = [...new Set(backlinks)];

  els.modalContent.innerHTML = `
    <div class="modal-head">
      <div><span class="modal-head-label">Evidence receipt</span><h2 id="modalTitle">${item.id} · ${item.source}</h2></div>
      <button class="icon-button modal-close" data-close-modal aria-label="Đóng">${icon("close")}</button>
    </div>
    <div class="modal-body">
      <div class="receipt-proof">
        <div class="proof-meta">
          <span class="proof-author"><span class="avatar ${person.className}">${person.initials}</span>${person.name}</span>
          <span>${item.timestamp} · ${item.channel}</span>
        </div>
        <blockquote>“${proof}”</blockquote>
        <div class="proof-context">${item.context}</div>
      </div>
      <div class="receipt-fields">
        <div class="receipt-field"><span>Pinned revision</span><strong>${item.revision}</strong></div>
        <div class="receipt-field"><span>Citation role</span><strong>${item.role}</strong></div>
        <div class="receipt-field"><span>Source locator</span><strong>${item.locator}</strong></div>
        <div class="receipt-field"><span>Content hash</span><strong>${item.hash}</strong></div>
      </div>
      <h3 class="backlink-heading">Backlinks · used by ${uniqueBacklinks.length} records</h3>
      ${uniqueBacklinks.map((link) => {
        const [id, label] = link.split(" · ");
        return `<div class="backlink-row">${icon(id.startsWith("D-") ? "decision" : id.startsWith("T-") ? "task" : "link")}<div><strong>${id}</strong><small>${label || "Related record"}</small></div>${icon("chevron")}</div>`;
      }).join("")}
    </div>
    <div class="modal-actions">
      <button class="secondary-button" data-close-modal>Close</button>
      <button class="primary-button" data-source-link>${icon("external")} Open source message</button>
    </div>`;
  els.evidenceModal.classList.add("open");
  els.evidenceModal.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";
}

function closeEvidence() {
  els.evidenceModal.classList.remove("open");
  els.evidenceModal.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
}

function getDocumentSearchParts(doc) {
  const sectionContent = (doc.sections || []).flatMap((section) => [
    section.title,
    ...(section.paragraphs || []),
    ...(section.bullets || []),
  ]);
  const evidenceContent = (doc.evidenceIds || [])
    .map((id) => evidence[id]?.text)
    .filter(Boolean);
  return [
    doc.title,
    doc.shortTitle,
    doc.description,
    doc.lead,
    doc.group,
    ...(doc.tags || []),
    ...sectionContent,
    ...evidenceContent,
    ...(doc.relatedTasks || []),
    ...(doc.relatedDecisions || []),
  ].filter(Boolean);
}

function getDocumentSearchSnippet(doc, query) {
  const parts = getDocumentSearchParts(doc);
  if (!query) return doc.description;
  const match = parts.find((part) => part.toLowerCase().includes(query));
  if (!match) return doc.description;
  return match.length > 92 ? `${match.slice(0, 89)}…` : match;
}

function getSearchItems(query = "") {
  const normalized = query.trim().toLowerCase();
  const items = [
    ...knowledgeDocs.map((doc) => ({
      type: "document",
      id: doc.id,
      title: doc.title,
      detail: `${doc.group} · ${getDocumentSearchSnippet(doc, normalized)}`,
      haystack: getDocumentSearchParts(doc).join(" "),
    })),
    ...tasks.map((task) => ({ type: "task", id: task.id, title: task.title, detail: `${statusLabel(task.status)} · ${task.decisionIds.length} decisions`, haystack: `${task.id} ${task.title} ${task.summary}` })),
    ...Object.values(decisions).map((decision) => ({ type: "decision", id: decision.id, title: decision.title, detail: `${decision.status} · ${decision.taskIds.join(", ")}`, haystack: `${decision.id} ${decision.title} ${decision.summary} ${decision.taskIds.join(" ")}` })),
    ...Object.values(evidence).map((item) => ({ type: "evidence", id: item.id, title: item.text, detail: `${item.source} · ${item.timestamp}`, haystack: `${item.id} ${item.text} ${item.source} ${item.author}` })),
  ];
  return items.filter((item) => !normalized || item.haystack.toLowerCase().includes(normalized)).slice(0, 9);
}

function renderSearchResults(query = "") {
  const results = getSearchItems(query);
  if (!results.length) {
    els.searchResults.innerHTML = `<div class="empty-search">Không tìm thấy kết quả phù hợp.<br/>Thử “LED”, “Kim Long” hoặc “T-02”.</div>`;
    return;
  }
  const grouped = results.reduce((acc, item) => {
    (acc[item.type] ||= []).push(item);
    return acc;
  }, {});
  els.searchResults.innerHTML = Object.entries(grouped).map(([type, items]) => `
    <div class="search-group-label">${type === "document" ? "Knowledge documents" : type === "task" ? "Tasks" : type === "decision" ? "Decisions" : "Evidence"}</div>
    ${items.map((item, index) => `
      <button class="search-result ${index === 0 && type === Object.keys(grouped)[0] ? "active" : ""}" data-search-type="${item.type}" data-search-id="${item.id}">
        <span class="search-result-icon ${item.type}">${icon(item.type === "document" ? "evidence" : item.type)}</span>
        <span class="search-result-copy"><strong>${item.id} · ${item.title}</strong><small>${item.detail}</small></span>
        <span class="search-result-kind">${item.type}</span>
      </button>`).join("")}`).join("");
}

function openSearch(initialQuery = "") {
  els.searchOverlay.classList.add("open");
  els.searchOverlay.setAttribute("aria-hidden", "false");
  els.searchInput.value = initialQuery;
  renderSearchResults(initialQuery);
  document.body.style.overflow = "hidden";
  window.setTimeout(() => els.searchInput.focus(), 50);
}

function closeSearch() {
  els.searchOverlay.classList.remove("open");
  els.searchOverlay.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
}

function chooseSearchResult(type, id) {
  closeSearch();
  if (type === "document") {
    state.selectedDocId = id;
    setView("knowledge");
  }
  if (type === "task") {
    setView("map");
    selectTask(id);
  }
  if (type === "decision") {
    const decision = decisions[id];
    setView("map");
    if (decision?.taskIds[0]) selectTask(decision.taskIds[0]);
    openDecision(id);
  }
  if (type === "evidence") openEvidence(id);
}

function showToast(message) {
  els.toast.querySelector("span").textContent = message;
  els.toast.classList.add("show");
  window.clearTimeout(showToast.timeout);
  showToast.timeout = window.setTimeout(() => els.toast.classList.remove("show"), 2200);
}

function closeSidebar() {
  els.sidebar.classList.remove("open");
  els.sidebarScrim.classList.remove("open");
}

document.addEventListener("click", (event) => {
  if (event.target.closest("[data-close-decision]")) {
    closeDecisionInspector();
    return;
  }

  const docTarget = event.target.closest("[data-doc-id]");
  if (docTarget) {
    state.selectedDocId = docTarget.dataset.docId;
    if (state.currentView !== "knowledge") setView("knowledge");
    else renderKnowledgeView();
    return;
  }

  const openTaskTarget = event.target.closest("[data-open-task]");
  if (openTaskTarget) {
    setView("map");
    selectTask(openTaskTarget.dataset.openTask);
    return;
  }

  const openDecisionTarget = event.target.closest("[data-open-decision]");
  if (openDecisionTarget) {
    const decision = decisions[openDecisionTarget.dataset.openDecision];
    setView("map");
    if (decision?.taskIds[0]) selectTask(decision.taskIds[0]);
    openDecision(openDecisionTarget.dataset.openDecision);
    return;
  }

  const taskTarget = event.target.closest("[data-task-id]");
  if (taskTarget) {
    selectTask(taskTarget.dataset.taskId);
    closeSidebar();
    return;
  }

  const decisionTarget = event.target.closest("[data-decision-id]");
  if (decisionTarget) {
    openDecision(decisionTarget.dataset.decisionId);
    return;
  }

  const evidenceTarget = event.target.closest("[data-evidence-id]");
  if (evidenceTarget) {
    openEvidence(evidenceTarget.dataset.evidenceId);
    return;
  }

  const searchResult = event.target.closest("[data-search-type]");
  if (searchResult) {
    chooseSearchResult(searchResult.dataset.searchType, searchResult.dataset.searchId);
    return;
  }

  const viewSwitch = event.target.closest("[data-view-switch]");
  if (viewSwitch) setView(viewSwitch.dataset.viewSwitch);

  if (event.target.closest("[data-close-search]")) closeSearch();
  if (event.target.closest("[data-close-modal]")) closeEvidence();
  if (event.target.closest("[data-source-link]")) showToast("Demo: đã mở deep link tới source message");
  if (event.target.closest("[data-copy-task]")) showToast(`Đã sao chép link ${state.selectedTaskId}`);
  if (event.target.closest("[data-copy-decision]")) showToast(`Đã sao chép link ${state.selectedDecisionId}`);
});

document.addEventListener("change", (event) => {
  if (event.target.id === "showInactive") {
    state.showInactive = event.target.checked;
    renderInspector();
  }
});

document.addEventListener("input", (event) => {
  if (event.target.id !== "kbDocFilter") return;
  const query = event.target.value.trim().toLowerCase();
  document.querySelectorAll(".kb-nav-group:not(.kb-collections)").forEach((group) => {
    const links = [...group.querySelectorAll(".kb-doc-link")];
    links.forEach((link) => {
      const doc = knowledgeDocs.find((item) => item.id === link.dataset.docId);
      link.hidden = Boolean(query && doc && !getDocumentSearchParts(doc).join(" ").toLowerCase().includes(query));
    });
    group.hidden = links.length > 0 && links.every((link) => link.hidden);
  });
});

document.addEventListener("keydown", (event) => {
  const target = event.target;
  const typing = target.matches("input, textarea, [contenteditable='true']");
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    openSearch();
  }
  if (!typing && event.key === "/") {
    event.preventDefault();
    openSearch();
  }
  if (event.key === "Escape") {
    closeSearch();
    closeEvidence();
    closeSidebar();
  }
  if ((event.key === "Enter" || event.key === " ") && target.matches(".task-node, .decision-card")) {
    event.preventDefault();
    target.click();
  }
  if (event.key === "Enter" && els.searchOverlay.classList.contains("open")) {
    const active = els.searchResults.querySelector(".search-result.active") || els.searchResults.querySelector(".search-result");
    if (active) active.click();
  }
});

document.querySelectorAll(".view-tab").forEach((tab) => tab.addEventListener("click", () => setView(tab.dataset.view)));
document.querySelectorAll(".nav-item[data-view]").forEach((item) => item.addEventListener("click", () => setView(item.dataset.view)));
document.getElementById("searchTrigger").addEventListener("click", () => openSearch());
document.getElementById("askButton").addEventListener("click", () => openSearch("Vì sao đổi sang đèn LED?"));
document.getElementById("shareButton").addEventListener("click", () => showToast("Đã sao chép liên kết project knowledge"));
document.getElementById("fitView").addEventListener("click", () => {
  setView("map");
  showToast("Đã đưa knowledge map về vị trí ban đầu");
});
document.getElementById("teamFilter").addEventListener("click", () => showToast("Demo đang lọc theo Events team"));
document.getElementById("mobileMenu").addEventListener("click", () => {
  els.sidebar.classList.add("open");
  els.sidebarScrim.classList.add("open");
});
document.getElementById("sidebarClose").addEventListener("click", closeSidebar);
els.sidebarScrim.addEventListener("click", closeSidebar);
els.searchInput.addEventListener("input", (event) => renderSearchResults(event.target.value));

setView("knowledge");
