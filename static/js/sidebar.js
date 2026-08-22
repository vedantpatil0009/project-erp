(() => {
    const sidebar = document.querySelector(".sidebar");
    if (!sidebar) return;

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "sidebar-toggle";
    toggle.setAttribute("aria-label", "Toggle sidebar");
    sidebar.appendChild(toggle);

    const storageKey = "educonSidebarCollapsed";
    const isSmallScreen = () => window.matchMedia("(max-width: 900px)").matches;

    const readCollapsedPreference = () => {
        try {
            return localStorage.getItem(storageKey) === "true";
        } catch (_) {
            return false;
        }
    };

    const saveCollapsedPreference = (collapsed) => {
        try {
            localStorage.setItem(storageKey, String(collapsed));
        } catch (_) {
            // The sidebar still works when browser storage is unavailable.
        }
    };

    const updateToggle = () => {
        const expanded = isSmallScreen()
            ? document.body.classList.contains("sidebar-expanded")
            : !document.body.classList.contains("sidebar-collapsed");
        toggle.setAttribute("aria-expanded", String(expanded));
        toggle.innerHTML = `<i class="fa-solid fa-angle-${expanded ? "left" : "right"}"></i>`;
    };

    const applyScreenState = () => {
        if (isSmallScreen()) {
            document.body.classList.remove("sidebar-collapsed");
        } else {
            document.body.classList.remove("sidebar-expanded");
            document.body.classList.toggle("sidebar-collapsed", readCollapsedPreference());
        }
        updateToggle();
    };

    toggle.addEventListener("click", () => {
        if (isSmallScreen()) {
            document.body.classList.toggle("sidebar-expanded");
        } else {
            const collapsed = !document.body.classList.contains("sidebar-collapsed");
            document.body.classList.toggle("sidebar-collapsed", collapsed);
            saveCollapsedPreference(collapsed);
        }
        updateToggle();
    });

    window.addEventListener("resize", applyScreenState);
    applyScreenState();
})();
