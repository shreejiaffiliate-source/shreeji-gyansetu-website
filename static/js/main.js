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
