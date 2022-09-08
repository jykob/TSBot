"use strict";
(() => {
    document.addEventListener("DOMContentLoaded", () => {
        const externalLinks = document.querySelectorAll("a.external");
        for (const link of externalLinks) {
            link.target = "_blank";
        }
    });
})();
