const toggleTheme = () => {
  const html = document.documentElement;
  const themeIcon = document.querySelector("#theme-toggle i");
  const currentTheme = html.getAttribute("data-theme");
  const newTheme = currentTheme === "dark" ? "light" : "dark";

  html.setAttribute("data-theme", newTheme);
  localStorage.setItem("theme", newTheme);

  // Update Icon visually
  if (themeIcon) {
    themeIcon.className = newTheme === "dark" ? "fas fa-sun" : "fas fa-moon";
  }
};

// Check for saved theme on page load
document.addEventListener("DOMContentLoaded", () => {
  const savedTheme = localStorage.getItem("theme") || "light";
  const themeIcon = document.querySelector("#theme-toggle i");

  document.documentElement.setAttribute("data-theme", savedTheme);

  // Set correct icon on load
  if (themeIcon) {
    themeIcon.className = savedTheme === "dark" ? "fas fa-sun" : "fas fa-moon";
  }
});

function updateThemeImage() {
  const img = document.getElementById("theme-aware-logo");
  if (!img) return;

  // Check if body has 'dark-mode' class or if data-theme is 'dark'
  // Adjust the 'document.body.classList.contains' to match your specific dark mode trigger
  const isDark =
    document.body.classList.contains("dark-mode") ||
    document.documentElement.getAttribute("data-theme") === "dark";

  if (isDark) {
    img.src = img.getAttribute("data-dark");
  } else {
    img.src = img.getAttribute("data-light");
  }
}

// 1. Run on page load
document.addEventListener("DOMContentLoaded", updateThemeImage);

// 2. Run whenever the theme toggle button is clicked
// Assuming your toggle button has an ID 'theme-toggle'
const toggleBtn = document.getElementById("theme-toggle");
if (toggleBtn) {
  toggleBtn.addEventListener("click", () => {
    // Wait a tiny bit for the class to be applied before checking
    setTimeout(updateThemeImage, 50);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  // 1. Handle Auto-hide
  const alerts = document.querySelectorAll(".alert-dismissible");
  alerts.forEach((alert) => {
    const autoHideTimeout = setTimeout(() => {
      dismissAlert(alert);
    }, 5000); // 5 seconds

    // 2. Handle Manual Close Button Click
    const closeBtn = alert.querySelector(".manual-close");
    if (closeBtn) {
      closeBtn.addEventListener("click", () => {
        clearTimeout(autoHideTimeout); // Stop the auto-hide timer if user clicks
        dismissAlert(alert);
      });
    }
  });

  // Helper function for smooth dismissal
  function dismissAlert(element) {
    element.style.transition = "all 0.4s ease";
    element.style.opacity = "0";
    element.style.transform = "translateX(-20px)";

    setTimeout(() => {
      element.remove();
    }, 4000);
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const toggleButtons = document.querySelectorAll(".toggle-password");

  toggleButtons.forEach((btn) => {
    btn.addEventListener("click", function () {
      const targetId = this.getAttribute("data-target");
      const passwordInput = document.getElementById(targetId);
      const icon = this.querySelector("i");

      if (passwordInput.type === "password") {
        passwordInput.type = "text";
        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");
      } else {
        passwordInput.type = "password";
        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");
      }
    });
  });
});
