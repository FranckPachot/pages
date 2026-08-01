(() => {
  "use strict";

  const catalog = window.PUBLICATION_CATALOG;
  const pageSize = 80;
  const state = {
    query: "",
    database: "",
    version: "",
    category: "",
    source: "",
    yearFrom: catalog.year_min,
    yearTo: catalog.year_max,
    sort: "newest",
    visible: pageSize,
  };

  const elements = {
    search: document.querySelector("#search"),
    database: document.querySelector("#database"),
    version: document.querySelector("#version"),
    category: document.querySelector("#category"),
    source: document.querySelector("#source"),
    yearFrom: document.querySelector("#year-from"),
    yearTo: document.querySelector("#year-to"),
    sort: document.querySelector("#sort"),
    results: document.querySelector("#results"),
    resultCount: document.querySelector("#result-count"),
    timeline: document.querySelector("#timeline"),
    activeFilters: document.querySelector("#active-filters"),
    emptyState: document.querySelector("#empty-state"),
    loadMore: document.querySelector("#load-more"),
    clearYear: document.querySelector("#clear-year"),
    reset: document.querySelector("#reset-filters"),
  };

  const sourceNames = Object.fromEntries(
    catalog.publications.map((publication) => [publication.source_key, publication.source]),
  );

  function option(select, value, label) {
    const element = document.createElement("option");
    element.value = value;
    element.textContent = label;
    select.append(element);
  }

  function populateOptions() {
    Object.entries(catalog.database_counts).forEach(([value, count]) => option(elements.database, value, `${value} · ${count}`));
    Object.entries(catalog.version_counts).forEach(([value, count]) => option(elements.version, value, `${value} · ${count}`));
    Object.entries(catalog.category_counts).forEach(([value, count]) => option(elements.category, value, `${value} · ${count}`));
    Object.entries(catalog.source_counts)
      .sort((left, right) => sourceNames[left[0]].localeCompare(sourceNames[right[0]]))
      .forEach(([value, count]) => option(elements.source, value, `${sourceNames[value]} · ${count}`));
    for (let year = catalog.year_min; year <= catalog.year_max; year += 1) {
      option(elements.yearFrom, String(year), String(year));
      option(elements.yearTo, String(year), String(year));
    }
  }

  function renderSummary() {
    const values = [
      ["Publications", catalog.publication_count.toLocaleString()],
      ["Years", `${catalog.year_min}–${catalog.year_max}`],
      ["Sources", Object.keys(catalog.source_counts).length],
      ["Database facets", Object.keys(catalog.database_counts).length - 1],
    ];
    const strip = document.querySelector("#summary-strip");
    values.forEach(([label, value]) => {
      const wrapper = document.createElement("div");
      const term = document.createElement("dt");
      const detail = document.createElement("dd");
      term.textContent = label;
      detail.textContent = value;
      wrapper.append(term, detail);
      strip.append(wrapper);
    });
    document.querySelector("#header-count").textContent = catalog.publication_count.toLocaleString();
    document.querySelector("#header-years").textContent = `${catalog.year_min}–${catalog.year_max}`;
  }

  function yearCounts(publications = catalog.publications) {
    return publications.reduce((counts, publication) => {
      counts[publication.year] = (counts[publication.year] || 0) + 1;
      return counts;
    }, {});
  }

  function renderTimeline(publications = catalog.publications) {
    const counts = yearCounts(publications);
    const maximum = Math.max(...Object.values(counts), 1);
    elements.timeline.replaceChildren();
    for (let year = catalog.year_min; year <= catalog.year_max; year += 1) {
      const count = counts[year] || 0;
      const button = document.createElement("button");
      button.type = "button";
      button.className = "year-bar";
      button.classList.toggle("is-active", state.yearFrom === year && state.yearTo === year);
      button.setAttribute("role", "listitem");
      button.setAttribute("aria-label", `${year}: ${count} publications`);
      button.innerHTML = `<span class="year-bar__count">${count}</span><span class="year-bar__column" style="height:${Math.max(4, (count / maximum) * 100)}%"></span><span>${year}</span>`;
      button.addEventListener("click", () => {
        state.yearFrom = year;
        state.yearTo = year;
        syncControls();
        update();
      });
      elements.timeline.append(button);
    }
  }

  function matches(publication) {
    const terms = state.query.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
    return terms.every((term) => publication.search_text.includes(term))
      && (!state.database || publication.databases.includes(state.database))
      && (!state.version || publication.versions.includes(state.version))
      && (!state.category || publication.categories.includes(state.category))
      && (!state.source || publication.source_key === state.source)
      && publication.year >= state.yearFrom
      && publication.year <= state.yearTo;
  }

  function filteredPublications() {
    const publications = catalog.publications.filter(matches);
    if (state.sort === "oldest") publications.sort((left, right) => left.date.localeCompare(right.date));
    if (state.sort === "title") publications.sort((left, right) => left.title.localeCompare(right.title));
    if (state.sort === "newest") publications.sort((left, right) => right.date.localeCompare(left.date));
    return publications;
  }

  function badge(value, modifier) {
    const element = document.createElement("span");
    element.className = `badge badge--${modifier}`;
    element.textContent = value;
    return element;
  }

  function publicationRow(publication) {
    const article = document.createElement("article");
    article.className = "publication";

    const date = document.createElement("time");
    date.className = "publication__date";
    date.dateTime = publication.date;
    date.textContent = publication.date;

    const body = document.createElement("div");
    const title = document.createElement("a");
    title.className = "publication__title";
    title.href = publication.read_url;
    title.textContent = publication.title;
    if (publication.read_url.startsWith("http")) {
      title.target = "_blank";
      title.rel = "noopener";
    }
    body.append(title);
    if (publication.summary) {
      const summary = document.createElement("p");
      summary.className = "publication__summary";
      summary.textContent = publication.summary;
      body.append(summary);
    }

    const metadata = document.createElement("div");
    metadata.className = "publication__meta";
    metadata.append(badge(publication.source, "source"));
    publication.databases.slice(0, 3).forEach((value) => metadata.append(badge(value, "database")));
    publication.versions.slice(0, 2).forEach((value) => metadata.append(badge(value, "version")));
    publication.categories.slice(0, 2).forEach((value) => metadata.append(badge(value, "category")));
    const snapshot = document.createElement("a");
    snapshot.className = "snapshot-link";
    snapshot.href = publication.archive_url;
    snapshot.textContent = "Snapshot ↗";
    metadata.append(snapshot);

    article.append(date, body, metadata);
    return article;
  }

  function activeFilterEntries() {
    const entries = [];
    if (state.query) entries.push(["query", `“${state.query}”`]);
    if (state.database) entries.push(["database", state.database]);
    if (state.version) entries.push(["version", state.version]);
    if (state.category) entries.push(["category", state.category]);
    if (state.source) entries.push(["source", sourceNames[state.source]]);
    if (state.yearFrom !== catalog.year_min || state.yearTo !== catalog.year_max) entries.push(["years", `${state.yearFrom}–${state.yearTo}`]);
    return entries;
  }

  function renderActiveFilters() {
    elements.activeFilters.replaceChildren();
    activeFilterEntries().forEach(([key, label]) => {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "filter-chip";
      chip.textContent = `${label} ×`;
      chip.addEventListener("click", () => clearFilter(key));
      elements.activeFilters.append(chip);
    });
  }

  function clearFilter(key) {
    if (key === "query") state.query = "";
    if (["database", "version", "category", "source"].includes(key)) state[key] = "";
    if (key === "years") {
      state.yearFrom = catalog.year_min;
      state.yearTo = catalog.year_max;
    }
    syncControls();
    update();
  }

  function syncControls() {
    elements.search.value = state.query;
    elements.database.value = state.database;
    elements.version.value = state.version;
    elements.category.value = state.category;
    elements.source.value = state.source;
    elements.yearFrom.value = String(state.yearFrom);
    elements.yearTo.value = String(state.yearTo);
    elements.sort.value = state.sort;
    elements.clearYear.hidden = state.yearFrom === catalog.year_min && state.yearTo === catalog.year_max;
  }

  function updateUrl() {
    const parameters = new URLSearchParams();
    if (state.query) parameters.set("q", state.query);
    ["database", "version", "category", "source"].forEach((key) => state[key] && parameters.set(key, state[key]));
    if (state.yearFrom !== catalog.year_min) parameters.set("from", state.yearFrom);
    if (state.yearTo !== catalog.year_max) parameters.set("to", state.yearTo);
    if (state.sort !== "newest") parameters.set("sort", state.sort);
    history.replaceState(null, "", `${location.pathname}${parameters.size ? `?${parameters}` : ""}`);
  }

  function update() {
    state.visible = Math.max(pageSize, state.visible);
    const publications = filteredPublications();
    elements.resultCount.textContent = publications.length.toLocaleString();
    elements.results.replaceChildren(...publications.slice(0, state.visible).map(publicationRow));
    elements.emptyState.hidden = publications.length !== 0;
    elements.loadMore.hidden = publications.length <= state.visible;
    elements.loadMore.textContent = `Show ${Math.min(pageSize, publications.length - state.visible)} more`;
    renderActiveFilters();
    renderTimeline(publications);
    updateUrl();
  }

  function readUrlState() {
    const parameters = new URLSearchParams(location.search);
    state.query = parameters.get("q") || "";
    ["database", "version", "category", "source"].forEach((key) => state[key] = parameters.get(key) || "");
    state.yearFrom = Number(parameters.get("from")) || catalog.year_min;
    state.yearTo = Number(parameters.get("to")) || catalog.year_max;
    state.sort = parameters.get("sort") || "newest";
  }

  function bindControls() {
    let searchFrame;
    elements.search.addEventListener("input", () => {
      cancelAnimationFrame(searchFrame);
      searchFrame = requestAnimationFrame(() => {
        state.query = elements.search.value;
        state.visible = pageSize;
        update();
      });
    });
    ["database", "version", "category", "source", "sort"].forEach((key) => {
      elements[key].addEventListener("change", () => {
        state[key] = elements[key].value;
        state.visible = pageSize;
        update();
      });
    });
    elements.yearFrom.addEventListener("change", () => {
      state.yearFrom = Number(elements.yearFrom.value);
      if (state.yearFrom > state.yearTo) state.yearTo = state.yearFrom;
      syncControls();
      update();
    });
    elements.yearTo.addEventListener("change", () => {
      state.yearTo = Number(elements.yearTo.value);
      if (state.yearTo < state.yearFrom) state.yearFrom = state.yearTo;
      syncControls();
      update();
    });
    elements.clearYear.addEventListener("click", () => clearFilter("years"));
    elements.reset.addEventListener("click", () => {
      Object.assign(state, { query: "", database: "", version: "", category: "", source: "", yearFrom: catalog.year_min, yearTo: catalog.year_max, sort: "newest", visible: pageSize });
      syncControls();
      update();
    });
    elements.loadMore.addEventListener("click", () => {
      state.visible += pageSize;
      update();
    });
  }

  populateOptions();
  renderSummary();
  readUrlState();
  syncControls();
  bindControls();
  update();
})();