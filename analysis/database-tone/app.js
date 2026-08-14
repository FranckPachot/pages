(() => {
  "use strict";

  const data = window.DATABASE_TONE_DATA;
  const elements = {
    database: document.querySelector("#database"),
    summary: document.querySelector("#database-summary"),
    chart: document.querySelector("#tone-chart"),
    matrixHead: document.querySelector("#matrix thead"),
    matrixBody: document.querySelector("#matrix tbody"),
    supportiveEvidence: document.querySelector("#supportive-evidence"),
    criticalEvidence: document.querySelector("#critical-evidence"),
    tooltip: document.querySelector("#analysis-tooltip"),
  };
  const periods = [...data.employment_periods].reverse();
  const databaseNames = Object.keys(data.database_counts);
  const maximumPeriodMentions = Math.max(...Object.values(data.aggregates).flatMap((aggregate) => (
    Object.values(aggregate.periods).map((period) => period.count)
  )));
  const scoreClasses = {
    "-2": "strong-critical",
    "-1": "critical",
    0: "neutral",
    1: "supportive",
    2: "strong-supportive",
  };

  function periodLabel(period) {
    return `${period.company} · ${period.range}`;
  }

  function percent(value) {
    return `${(value * 100).toFixed(1)}%`;
  }

  function formatScore(value) {
    return `${value > 0 ? "+" : ""}${value.toFixed(2)}`;
  }

  function placeTooltip(target) {
    const targetBox = target.getBoundingClientRect();
    const tooltipBox = elements.tooltip.getBoundingClientRect();
    const left = Math.max(12, Math.min(innerWidth - tooltipBox.width - 12, targetBox.left + targetBox.width / 2 - tooltipBox.width / 2));
    const below = targetBox.bottom + 9;
    const top = below + tooltipBox.height <= innerHeight - 12 ? below : targetBox.top - tooltipBox.height - 9;
    elements.tooltip.style.left = `${left}px`;
    elements.tooltip.style.top = `${Math.max(12, top)}px`;
  }

  function attachTooltip(target, text) {
    target.tabIndex = 0;
    target.setAttribute("aria-describedby", "analysis-tooltip");
    const show = () => {
      elements.tooltip.textContent = text;
      elements.tooltip.hidden = false;
      placeTooltip(target);
    };
    const hide = () => {
      elements.tooltip.hidden = true;
    };
    target.addEventListener("mouseenter", show);
    target.addEventListener("mouseleave", hide);
    target.addEventListener("focus", show);
    target.addEventListener("blur", hide);
  }

  function recordsFor(database, periodKey, evaluation = null) {
    return data.records.filter((record) => (
      record.database === database
      && record.employment_period === periodKey
      && (evaluation === null || record.evaluation === evaluation)
    ));
  }

  function recordLines(records, limit = 4) {
    const normalizeComparison = (value) => value.toLocaleLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
    const lines = records.slice(0, limit).map((record) => {
      const excerpt = normalizeComparison(record.evidence_excerpt) === normalizeComparison(record.title)
        ? ""
        : `\n  ${record.evidence_excerpt}`;
      return `• ${record.title}${excerpt}`;
    });
    if (records.length > limit) lines.push(`• ${records.length - limit} more`);
    return lines;
  }

  function periodTooltip(database, period, values) {
    const records = recordsFor(database, period.key);
    const critical = records.filter((record) => record.evaluation < 0);
    const supportive = records.filter((record) => record.evaluation > 0);
    const neutral = records.length - critical.length - supportive.length;
    const lines = [
      `${database} · ${periodLabel(period)}`,
      `${records.length} mentions analyzed`,
      `${critical.length} critical · ${neutral} neutral · ${supportive.length} supportive`,
    ];
    if (critical.length) lines.push("", "Critical framing:", ...recordLines(critical, 3));
    if (supportive.length) lines.push("", "Supportive framing:", ...recordLines(supportive, 3));
    if (!critical.length && !supportive.length) lines.push("", "No explicitly critical or supportive framing.");
    return lines.join("\n");
  }

  function populateDatabases() {
    databaseNames.forEach((database) => {
      const option = document.createElement("option");
      option.value = database;
      option.textContent = `${database} · ${data.database_counts[database]} mentions`;
      elements.database.append(option);
    });
    const requested = new URLSearchParams(location.search).get("database");
    elements.database.value = databaseNames.includes(requested) ? requested : "Oracle Database";
  }

  function databaseSummary(database) {
    const aggregate = data.aggregates[database];
    const substantial = Object.values(aggregate.periods).filter((period) => period.count >= 10);
    if (!substantial.length) {
      return `${database} has ${aggregate.count} explicit mentions, but no employment period has the 10 records needed for a stable comparison.`;
    }
    const minimum = Math.min(...substantial.map((period) => period.mean_evaluation));
    const maximum = Math.max(...substantial.map((period) => period.mean_evaluation));
    const productWideCritical = substantial.reduce((total, period) => total + period.product_wide_critical_count, 0);
    return `${database} has ${aggregate.count} explicit mentions. Across periods with at least 10 records, the average framing score ranges from ${formatScore(minimum)} to ${formatScore(maximum)} on the −2 to +2 scale. ${productWideCritical} critical ${productWideCritical === 1 ? "record makes" : "records make"} a product-wide claim.`;
  }

  function renderChart(database) {
    const aggregate = data.aggregates[database];
    elements.summary.textContent = databaseSummary(database);
    elements.chart.replaceChildren();
    periods.forEach((period) => {
      const values = aggregate.periods[period.key];
      if (!values) return;
      const row = document.createElement("div");
      row.className = `tone-row${values.count < 10 ? " small-sample" : ""}`;

      const label = document.createElement("div");
      label.className = "tone-row__label";
      label.innerHTML = `<strong>${period.company}</strong><span>${period.range}${values.count < 10 ? " · small sample" : ""}</span>`;

      const plot = document.createElement("div");
      plot.className = "tone-row__plot";
      const bar = document.createElement("div");
      bar.className = "tone-bar";
      bar.setAttribute("aria-label", `${periodLabel(period)}: ${values.count} mentions, ${percent(values.supportive_share)} supportive, ${percent(values.critical_share)} critical`);
      [-2, -1, 0, 1, 2].forEach((score) => {
        const segment = document.createElement("span");
        segment.className = `tone-bar__${scoreClasses[score]}`;
        segment.style.width = `${(values.distribution[score] / values.count) * 100}%`;
        const segmentRecords = recordsFor(database, period.key, score);
        if (segmentRecords.length) {
          const label = `${score > 0 ? "+" : ""}${score} ${scoreClasses[score].replace("-", " ")}`;
          attachTooltip(segment, [
            `${segmentRecords.length} ${label} ${segmentRecords.length === 1 ? "mention" : "mentions"}`,
            ...recordLines(segmentRecords),
          ].join("\n"));
        }
        bar.append(segment);
      });
      const axis = document.createElement("div");
      axis.className = "mean-axis";
      const marker = document.createElement("i");
      marker.style.setProperty("--position", `${((values.mean_evaluation + 2) / 4) * 100}%`);
      marker.title = `Average framing score ${formatScore(values.mean_evaluation)}`;
      axis.append(marker);
      plot.append(bar, axis);

      const score = document.createElement("div");
      score.className = "tone-row__score";
      score.innerHTML = `<strong>${formatScore(values.mean_evaluation)}</strong><span>average framing</span><span>${values.count} mentions analyzed</span>`;
      row.append(label, plot, score);
      elements.chart.append(row);
    });
  }

  function blendColor(start, end, amount) {
    const channels = start.map((value, index) => Math.round(value + (end[index] - value) * amount));
    return `rgb(${channels.join(", ")})`;
  }

  function cellColor(score, count) {
    const volumeRange = Math.max(1, maximumPeriodMentions - 1);
    const volume = .04 + .96 * Math.sqrt(Math.max(0, count - 1) / volumeRange);
    const gray = [222, 220, 212];
    const tone = score < 0 ? [226, 74, 74] : score > 0 ? [53, 201, 111] : [33, 135, 199];
    const scoreEmphasis = score === 0 ? 1 : Math.min(1, .45 + Math.abs(score) / 2);
    return blendColor(gray, tone, Math.min(1, volume * scoreEmphasis));
  }

  function renderMatrix() {
    const row = document.createElement("tr");
    const corner = document.createElement("th");
    corner.textContent = "Database";
    row.append(corner, ...periods.map((period) => {
      const heading = document.createElement("th");
      heading.textContent = periodLabel(period);
      return heading;
    }));
    elements.matrixHead.replaceChildren(row);

    elements.matrixBody.replaceChildren(...databaseNames.map((database) => {
      const tableRow = document.createElement("tr");
      const heading = document.createElement("th");
      heading.scope = "row";
      heading.textContent = database;
      tableRow.append(heading);
      periods.forEach((period) => {
        const cell = document.createElement("td");
        const values = data.aggregates[database].periods[period.key];
        if (!values) {
          cell.className = "empty";
          cell.textContent = "—";
        } else {
          cell.style.setProperty("--cell-color", cellColor(values.mean_evaluation, values.count));
          cell.classList.toggle("low-sample", values.count < 10);
          cell.innerHTML = `${formatScore(values.mean_evaluation)}<small>${values.count} mentions</small>`;
          attachTooltip(cell, periodTooltip(database, period, values));
        }
        tableRow.append(cell);
      });
      return tableRow;
    }));
  }

  function evidenceItem(record) {
    const item = document.createElement("article");
    item.className = "evidence-item";
    const link = document.createElement("a");
    link.href = record.url;
    link.textContent = record.title;
    if (record.url.startsWith("http")) {
      link.target = "_blank";
      link.rel = "noopener";
    }
    const excerpt = document.createElement("p");
    excerpt.textContent = record.evidence_excerpt;
    const meta = document.createElement("span");
    const period = data.employment_periods.find((candidate) => candidate.key === record.employment_period);
    meta.textContent = `${record.date} · ${period.company} · score ${record.evaluation > 0 ? "+" : ""}${record.evaluation} · ${record.scope}`;
    item.append(link, excerpt, meta);
    return item;
  }

  function renderEvidence(database) {
    const records = data.records.filter((record) => record.database === database);
    const supportive = records
      .filter((record) => record.evaluation > 0)
      .sort((left, right) => right.evaluation - left.evaluation || right.positive_weight - left.positive_weight)
      .slice(0, 5);
    const critical = records
      .filter((record) => record.evaluation < 0)
      .sort((left, right) => left.evaluation - right.evaluation || right.critical_weight - left.critical_weight)
      .slice(0, 5);
    elements.supportiveEvidence.replaceChildren(...supportive.map(evidenceItem));
    elements.criticalEvidence.replaceChildren(...critical.map(evidenceItem));
    if (!supportive.length) elements.supportiveEvidence.textContent = "No explicit supportive framing in this sample.";
    if (!critical.length) elements.criticalEvidence.textContent = "No explicit critical framing in this sample.";
  }

  function update() {
    const database = elements.database.value;
    renderChart(database);
    renderEvidence(database);
    const parameters = new URLSearchParams(location.search);
    if (database === "Oracle Database") parameters.delete("database");
    else parameters.set("database", database);
    history.replaceState(null, "", `${location.pathname}${parameters.size ? `?${parameters}` : ""}`);
  }

  populateDatabases();
  renderMatrix();
  elements.database.addEventListener("change", update);
  update();
})();
