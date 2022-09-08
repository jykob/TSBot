(() => {
  document.addEventListener("DOMContentLoaded", () => {
    const externalLinks = document.querySelectorAll("a.external") as NodeListOf<HTMLAnchorElement>;

    for (const link of externalLinks) {
      link.target = "_blank";
    }
  });
})();
