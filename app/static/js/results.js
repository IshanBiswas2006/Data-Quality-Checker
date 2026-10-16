document.addEventListener("DOMContentLoaded", () => {
  const analysisId = document.body.dataset.analysisId;
  if (!analysisId) return;

  // 1. Tab Navigation
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");

  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.tab;
      
      tabButtons.forEach((b) => b.classList.remove("active"));
      tabPanes.forEach((p) => p.classList.remove("active"));
      
      btn.classList.add("active");
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add("active");
    });
  });

  // 2. Modal Setup
  const confirmModal = document.getElementById("confirmModal");
  const modalTitle = document.getElementById("modalTitle");
  const modalMessage = document.getElementById("modalMessage");
  const modalActionBtn = document.getElementById("modalActionBtn");
  const modalCancelBtn = document.getElementById("modalCancelBtn");
  const modalCloseBtn = document.getElementById("modalCloseBtn");

  let pendingOperation = null;

  function openConfirmModal(title, message, isDestructive, onConfirm) {
    if (!confirmModal) return;
    modalTitle.textContent = title;
    modalMessage.textContent = message;
    
    if (isDestructive) {
      modalActionBtn.className = "btn btn-danger";
      modalActionBtn.textContent = "Confirm & Apply";
    } else {
      modalActionBtn.className = "btn btn-accent";
      modalActionBtn.textContent = "Apply";
    }
    
    pendingOperation = onConfirm;
    confirmModal.classList.add("active");
  }

  function closeModal() {
    if (confirmModal) confirmModal.classList.remove("active");
    pendingOperation = null;
  }

  if (modalCloseBtn) modalCloseBtn.addEventListener("click", closeModal);
  if (modalCancelBtn) modalCancelBtn.addEventListener("click", closeModal);
  if (modalActionBtn) {
    modalActionBtn.addEventListener("click", () => {
      if (pendingOperation) {
        pendingOperation();
      }
      closeModal();
    });
  }

  // 3. Cleaning Operations Execution
  async function executeCleanOp(opPayload, btnElement) {
    let originalHtml = "";
    if (btnElement) {
      originalHtml = btnElement.innerHTML;
      btnElement.disabled = true;
      btnElement.innerHTML = `<span class="spinner"></span> Applying...`;
    }

    try {
      const response = await fetch(`/clean/${analysisId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest"
        },
        body: JSON.stringify(opPayload)
      });

      const res = await response.json();
      if (!response.ok || !res.success) {
        showToast(res.error || "Failed to apply operation.", "error");
        if (btnElement) {
          btnElement.disabled = false;
          btnElement.innerHTML = originalHtml;
        }
        return;
      }

      showToast(res.message, "success");
      // Reload page to refresh all tabs, comparisons, tables and charts
      window.location.reload();
    } catch (err) {
      showToast("Network error while applying cleaning operation.", "error");
      if (btnElement) {
        btnElement.disabled = false;
        btnElement.innerHTML = originalHtml;
      }
    }
  }

  // Hook up cleaning forms & buttons
  // 3a. Remove Duplicates
  const btnRemoveDups = document.getElementById("btnRemoveDups");
  if (btnRemoveDups) {
    btnRemoveDups.addEventListener("click", () => {
      openConfirmModal(
        "Remove Duplicate Rows",
        "This will permanently drop exact duplicate records from the working dataset. The original file remains safe.",
        true,
        () => executeCleanOp({ type: "remove_duplicates", params: {} }, btnRemoveDups)
      );
    });
  }

  // 3b. Remove Missing Rows Form
  const formRemoveMissing = document.getElementById("formRemoveMissing");
  if (formRemoveMissing) {
    formRemoveMissing.addEventListener("submit", (e) => {
      e.preventDefault();
      const col = document.getElementById("removeMissingCol").value;
      const how = document.getElementById("removeMissingHow").value;
      const targetDesc = col === "__all__" ? `any row where ${how} column is missing` : `rows where column '${col}' is missing`;
      
      openConfirmModal(
        "Remove Rows with Missing Values",
        `Are you sure you want to remove ${targetDesc}?`,
        true,
        () => executeCleanOp({ type: "remove_missing_rows", params: { column: col, how: how } }, formRemoveMissing.querySelector("button[type=submit]"))
      );
    });
  }

  // 3c. Fill Missing Values Form
  const formFillMissing = document.getElementById("formFillMissing");
  const fillColSelect = document.getElementById("fillColSelect");
  const fillStrategy = document.getElementById("fillStrategy");
  const fillValGroup = document.getElementById("fillValGroup");
  const fillValInput = document.getElementById("fillValInput");

  if (fillStrategy && fillValGroup) {
    fillStrategy.addEventListener("change", () => {
      if (fillStrategy.value === "constant") {
        fillValGroup.style.display = "block";
      } else {
        fillValGroup.style.display = "none";
      }
    });
  }

  if (formFillMissing) {
    formFillMissing.addEventListener("submit", (e) => {
      e.preventDefault();
      const col = fillColSelect.value;
      const strategy = fillStrategy.value;
      const val = fillValInput.value.trim();

      if (strategy === "constant" && !val) {
        showToast("Please enter a constant value to fill.", "warning");
        return;
      }

      openConfirmModal(
        "Fill Missing Values",
        `Fill missing values in column '${col}' using strategy: ${strategy} (${val || "computed"})?`,
        false,
        () => executeCleanOp({
          type: "fill_missing",
          params: { column: col, strategy: strategy, value: val }
        }, formFillMissing.querySelector("button[type=submit]"))
      );
    });
  }

  // 3d. Convert Type Form
  const formConvertType = document.getElementById("formConvertType");
  if (formConvertType) {
    formConvertType.addEventListener("submit", (e) => {
      e.preventDefault();
      const col = document.getElementById("convertColSelect").value;
      const targetType = document.getElementById("convertTargetType").value;

      openConfirmModal(
        "Convert Column Data Type",
        `Convert column '${col}' to type '${targetType}'? Non-convertible values will be handled safely.`,
        false,
        () => executeCleanOp({
          type: "convert_type",
          params: { column: col, target_type: targetType }
        }, formConvertType.querySelector("button[type=submit]"))
      );
    });
  }

  // 3e. Strip Whitespace Form
  const formStripWhitespace = document.getElementById("formStripWhitespace");
  if (formStripWhitespace) {
    formStripWhitespace.addEventListener("submit", (e) => {
      e.preventDefault();
      const col = document.getElementById("stripColSelect").value;
      executeCleanOp({
        type: "strip_whitespace",
        params: { column: col }
      }, formStripWhitespace.querySelector("button[type=submit]"));
    });
  }

  // 3f. Drop Column Form
  const formDropCol = document.getElementById("formDropCol");
  if (formDropCol) {
    formDropCol.addEventListener("submit", (e) => {
      e.preventDefault();
      const col = document.getElementById("dropColSelect").value;
      openConfirmModal(
        "Drop Column",
        `Are you sure you want to permanently drop column '${col}' from the cleaned dataset?`,
        true,
        () => executeCleanOp({
          type: "drop_column",
          params: { column: col }
        }, formDropCol.querySelector("button[type=submit]"))
      );
    });
  }

  // 4. Reset Working Copy
  const btnReset = document.getElementById("btnResetDataset");
  if (btnReset) {
    btnReset.addEventListener("click", () => {
      openConfirmModal(
        "Reset Working Dataset",
        "This will discard all cleaning operations and restore the original uploaded data. Are you sure?",
        true,
        async () => {
          try {
            const resp = await fetch(`/reset/${analysisId}`, {
              method: "POST",
              headers: { "X-Requested-With": "XMLHttpRequest" }
            });
            const data = await resp.json();
            if (data.success) {
              showToast(data.message, "info");
              window.location.reload();
            } else {
              showToast(data.error || "Reset failed.", "error");
            }
          } catch (e) {
            showToast("Network error during reset.", "error");
          }
        }
      );
    });
  }

  // 5. Validation Rules Runner
  const btnRunValidation = document.getElementById("btnRunValidation");
  if (btnRunValidation) {
    btnRunValidation.addEventListener("click", async () => {
      const ruleCheckboxes = document.querySelectorAll(".rule-checkbox:checked");
      const activeRules = [];
      
      ruleCheckboxes.forEach((cb) => {
        try {
          const ruleData = JSON.parse(cb.dataset.rule);
          activeRules.push(ruleData);
        } catch (e) {}
      });

      btnRunValidation.disabled = true;
      btnRunValidation.innerHTML = `<span class="spinner"></span> Evaluating...`;

      try {
        const resp = await fetch(`/validate-rules/${analysisId}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Requested-With": "XMLHttpRequest"
          },
          body: JSON.stringify({ rules: activeRules })
        });
        const res = await resp.json();
        if (res.success) {
          showToast(`Evaluated ${res.validation.rules_evaluated} rules (${res.validation.total_violations} violations found).`, res.validation.total_violations === 0 ? "success" : "warning");
          renderValidationViolations(res.validation);
        }
      } catch (err) {
        showToast("Error executing validation rules.", "error");
      } finally {
        btnRunValidation.disabled = false;
        btnRunValidation.textContent = "Run Selected Rules";
      }
    });
  }

  function renderValidationViolations(validation) {
    const container = document.getElementById("validationResultsContainer");
    if (!container) return;

    if (validation.results.length === 0) {
      container.innerHTML = `<p style="color: var(--text-muted); padding: 12px 0;">No validation rules were selected.</p>`;
      return;
    }

    let html = `<div class="table-container"><table class="data-table"><thead><tr>
      <th>Status</th><th>Column</th><th>Rule Type</th><th>Violations</th><th>Sample Failed Values & Reason</th>
    </tr></thead><tbody>`;

    validation.results.forEach((r) => {
      const isPassed = r.status === "passed";
      const statusBadge = isPassed
        ? `<span class="badge badge-success">Passed (0)</span>`
        : `<span class="badge badge-danger">Failed (${r.violations_count})</span>`;
      
      let samplesHtml = "None";
      if (!isPassed && r.samples && r.samples.length > 0) {
        samplesHtml = `<ul style="list-style: none; margin: 0; padding: 0;">` +
          r.samples.slice(0, 3).map(s => `<li style="margin-bottom: 4px;"><strong>Row ${s.row_index}:</strong> '${s.value}' &mdash; <span style="color: var(--text-secondary);">${s.reason}</span></li>`).join("") +
          `</ul>`;
      }

      html += `<tr>
        <td>${statusBadge}</td>
        <td><strong>${r.column}</strong></td>
        <td><code>${r.type}</code></td>
        <td>${r.violations_count}</td>
        <td>${samplesHtml}</td>
      </tr>`;
    });

    html += `</tbody></table></div>`;
    container.innerHTML = html;
  }
});
