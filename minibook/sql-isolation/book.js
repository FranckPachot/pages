const progress = document.querySelector("#reading-progress");
const sections = [...document.querySelectorAll(".chapter[id]")];
const contentsLinks = [...document.querySelectorAll(".contents a")];

function updateReadingState() {
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const percentage = scrollable > 0 ? Math.min(100, (window.scrollY / scrollable) * 100) : 0;
  progress.style.width = `${percentage}%`;

  const current = [...sections].reverse().find((section) => section.getBoundingClientRect().top <= 150);
  contentsLinks.forEach((link) => {
    const isCurrent = current && link.hash === `#${current.id}`;
    if (isCurrent) {
      link.setAttribute("aria-current", "true");
    } else {
      link.removeAttribute("aria-current");
    }
  });
}

window.addEventListener("scroll", updateReadingState, { passive: true });
window.addEventListener("resize", updateReadingState);
updateReadingState();
