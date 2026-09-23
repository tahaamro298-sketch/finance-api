import "./style.css";

const revealElements = document.querySelectorAll(
  ".hero-content, .section-heading, .summary-card, .transactions-card, .transaction-row, .chart-card"
);

revealElements.forEach((element) => {
  element.classList.add("reveal");
});

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        observer.unobserve(entry.target);
      }
    });
  },
  {
    threshold: 0.15
  }
);

revealElements.forEach((element) => {
  observer.observe(element);
});