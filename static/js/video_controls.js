// static/js/video_controls.js

document.addEventListener("DOMContentLoaded", function () {
  const video = document.getElementById("courseVideo");

  if (video) {
    // Keyboard focus fix
    video.focus();

    document.addEventListener("keydown", function (event) {
      // 1. Prevent interference while typing in inputs, textareas, or contentEditable elements
      const isTyping =
        document.activeElement.tagName === "INPUT" ||
        document.activeElement.tagName === "TEXTAREA" ||
        document.activeElement.isContentEditable;

      if (!isTyping) {
        switch (event.key) {
          // Forward 10 seconds
          case "ArrowRight":
            event.preventDefault();
            video.currentTime = Math.min(
              video.duration,
              video.currentTime + 10,
            );
            break;

          // Backward 10 seconds
          case "ArrowLeft":
            event.preventDefault();
            video.currentTime = Math.max(0, video.currentTime - 10);
            break;

          // Play/Pause with Spacebar
          case " ":
            event.preventDefault();
            if (video.paused) {
              video.play();
            } else {
              video.pause();
            }
            break;

          // Volume Up with ArrowUp
          case "ArrowUp":
            event.preventDefault();
            video.volume = Math.min(1, video.volume + 0.1);
            break;

          // Volume Down with ArrowDown
          case "ArrowDown":
            event.preventDefault();
            video.volume = Math.max(0, video.volume - 0.1);
            break;

          // Mute toggle with 'm'
          case "m":
          case "M":
            video.muted = !video.muted;
            break;

          // Fullscreen toggle with 'f'
          case "f":
          case "F":
            if (!document.fullscreenElement) {
              video.requestFullscreen().catch((err) => {
                console.error(
                  `Error attempting to enable full-screen mode: ${err.message}`,
                );
              });
            } else {
              document.exitFullscreen();
            }
            break;
        }
      }
    });

    // 2. Extra Touch: Right Click Disable (Privacy)
    video.addEventListener(
      "contextmenu",
      function (e) {
        e.preventDefault();
      },
      false,
    );
  }
});
