// static/js/video_controls.js
document.addEventListener("DOMContentLoaded", function () {
  const video = document.getElementById("courseVideo");

  if (video) {
    video.focus();
    document.addEventListener("keydown", function (event) {
      // Prevent interference while typing in search bars or inputs
      const isTyping =
        document.activeElement.tagName === "INPUT" ||
        document.activeElement.tagName === "TEXTAREA";

      if (!isTyping) {
        if (event.key === "ArrowRight") {
          event.preventDefault();
          video.currentTime += 10;
        } else if (event.key === "ArrowLeft") {
          event.preventDefault();
          video.currentTime -= 10;
        } else if (event.key === " ") {
          event.preventDefault();
          if (video.paused) video.play();
          else video.pause();
        }
      }
    });
  }
});
