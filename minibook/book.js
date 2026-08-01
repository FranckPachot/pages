(() => {
  const progress = document.querySelector("#reading-progress");
  const links = [...document.querySelectorAll('.contents a[href^="#"]')];
  const sections = links
    .map((link) => document.querySelector(link.hash))
    .filter(Boolean);

  const updateProgress = () => {
    const available = document.documentElement.scrollHeight - window.innerHeight;
    const percent = available > 0 ? Math.min(100, (window.scrollY / available) * 100) : 0;
    progress.style.width = `${percent}%`;
  };

  const updateActiveSection = () => {
    const marker = window.scrollY + window.innerHeight * 0.3;
    const active = sections.reduce((current, section) => {
      const sectionTop = section.getBoundingClientRect().top + window.scrollY;
      return sectionTop <= marker ? section : current;
    }, sections[0]);
    links.forEach((link) => {
      if (link.hash === `#${active.id}`) link.setAttribute("aria-current", "true");
      else link.removeAttribute("aria-current");
    });
  };

  const updateReadingState = () => {
    updateProgress();
    updateActiveSection();
  };

  window.addEventListener("scroll", updateReadingState, { passive: true });
  updateProgress();
  updateActiveSection();
})();
