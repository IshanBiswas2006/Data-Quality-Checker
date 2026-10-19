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

  // 3. Dynamic color swatches & avatar badges
  document.querySelectorAll("[data-color]").forEach((el) => {
    if (el.dataset.color) el.style.backgroundColor = el.dataset.color;
  });

  // 4. Interactive Cloudflare-style verification widget (no auto-tick, no test messages)
  const captchaCard = document.getElementById("securityCaptchaCard");
  const captchaCheckbox = document.getElementById("captchaCheckbox");
  const captchaWrapper = document.getElementById("captchaCheckboxWrapper");
  const captchaLabel = document.getElementById("captchaLabel");
  const captchaInput = document.getElementById("captchaResponseInput");

  if (captchaCard && captchaCheckbox && captchaInput) {
    let isVerifying = false;
    let isVerified = false;

    const performVerification = () => {
      if (isVerifying || isVerified) return;
      isVerifying = true;
      captchaCheckbox.classList.add("verifying");
      if (captchaLabel) captchaLabel.textContent = "Verifying...";
      captchaCheckbox.setAttribute("aria-checked", "mixed");

      setTimeout(() => {
        isVerifying = false;
        isVerified = true;
        captchaCheckbox.classList.remove("verifying");
        captchaCheckbox.classList.add("verified");
        captchaCheckbox.setAttribute("aria-checked", "true");
        if (captchaLabel) {
          captchaLabel.textContent = "Success!";
          captchaLabel.style.color = "";
        }
        captchaInput.value = captchaInput.dataset.token || "verified";
        captchaCard.classList.remove("captcha-error");
      }, 550);
    };

    if (captchaWrapper) {
      captchaWrapper.addEventListener("click", performVerification);
    } else {
      captchaCheckbox.addEventListener("click", performVerification);
    }

    captchaCheckbox.addEventListener("keydown", (e) => {
      if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        performVerification();
      }
    });

    const parentForm = captchaCard.closest("form");
    if (parentForm) {
      parentForm.addEventListener("submit", (e) => {
        if (!captchaInput.value) {
          e.preventDefault();
          captchaCard.classList.add("captcha-error");
          if (captchaLabel) {
            captchaLabel.textContent = "Please verify you are human";
            captchaLabel.style.color = "var(--danger)";
            setTimeout(() => {
              captchaCard.classList.remove("captcha-error");
              if (!captchaInput.value) {
                captchaLabel.textContent = "Verify you are human";
                captchaLabel.style.color = "";
              }
            }, 2500);
          }
        }
      });
    }
  }
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
