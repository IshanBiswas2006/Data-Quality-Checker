// Global Application JavaScript
document.addEventListener("DOMContentLoaded", () => {
  // 1. Theme toggle
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  const htmlEl = document.documentElement;
  
  const savedTheme = localStorage.getItem("dqc_theme") || "dark";
  htmlEl.setAttribute("data-theme", savedTheme);
  updateThemeButtonText(savedTheme);
  
  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
      const currentTheme = htmlEl.getAttribute("data-theme") || "dark";
      const newTheme = currentTheme === "dark" ? "light" : "dark";
      htmlEl.setAttribute("data-theme", newTheme);
      localStorage.setItem("dqc_theme", newTheme);
      updateThemeButtonText(newTheme);
    });
  }
  
  function updateThemeButtonText(theme) {
    if (!themeToggleBtn) return;
    const label = themeToggleBtn.querySelector(".theme-label");
    if (label) {
      label.textContent = theme === "dark" ? "Light Mode" : "Dark Mode";
    }
  }

  // 2. Alert dismissal
  document.querySelectorAll(".alert-close").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      const alert = e.target.closest(".alert");
      if (alert) alert.remove();
    });
  });
});

// Toast notification utility
function showToast(message, type = "info") {
  const container = document.getElementById("alertsContainer");
  if (!container) return;
  
  const alert = document.createElement("div");
  alert.className = `alert alert-${type}`;
  alert.innerHTML = `
    <span>${message}</span>
    <button type="button" class="alert-close" aria-label="Close">&times;</button>
  `;
  
  alert.querySelector(".alert-close").addEventListener("click", () => alert.remove());
  container.prepend(alert);
  
  setTimeout(() => {
    if (alert.parentNode) alert.remove();
  }, 6000);
}
