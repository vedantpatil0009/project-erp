// ===================================
// EduSphere Parent Dashboard
// script.js
// ===================================

// Sidebar Active Menu

const menuItems = document.querySelectorAll(".sidebar ul li");

const parentSidebar = document.querySelector(".sidebar ul");
if (parentSidebar && !parentSidebar.querySelector('[data-settings-link]')) {
    const settingsItem = document.createElement("li");
    settingsItem.setAttribute("data-settings-link", "true");
    settingsItem.innerHTML = '<i class="fa-solid fa-gear"></i><span>Settings</span>';
    settingsItem.addEventListener("click", () => { window.location.href = "/parent/settings"; });
    const profile = parentSidebar.querySelector(".sidebar-profile");
    const logout = Array.from(parentSidebar.children).find(item => item.textContent.trim() === "Logout");
    parentSidebar.insertBefore(settingsItem, profile || logout || null);
}

const profileItem = document.querySelector(".sidebar-profile");
if (profileItem && !profileItem.getAttribute("onclick")) {
    profileItem.addEventListener("click", () => {
        window.location.href = "/parent/profile";
    });
}

menuItems.forEach(item => {

    item.addEventListener("click", () => {

        menuItems.forEach(i => i.classList.remove("active"));

        item.classList.add("active");

    });

});

// Welcome Message

window.onload = function(){

    console.log("Welcome to EduSphere Parent Dashboard");

};

// Render each connected child's current-day attendance in the dashboard card.
setTimeout(() => {
    const optionsNode = document.getElementById("parent-student-options");
    const overview = document.querySelector(".parent-overview-cards");
    if (optionsNode && overview && !document.querySelector(".parent-dashboard-student-selector")) {
        let options;
        try { options = JSON.parse(optionsNode.textContent || "[]"); } catch (_) { options = []; }
        const wrapper = document.createElement("section");
        wrapper.className = "box parent-dashboard-student-selector";
        wrapper.innerHTML = '<label for="parent-dashboard-student">Select Student</label><select id="parent-dashboard-student"></select>';
        const select = wrapper.querySelector("select");
        const current = new URLSearchParams(window.location.search).get("student_id");
        options.forEach(child => {
            const option = document.createElement("option");
            option.value = child.id;
            option.textContent = child.name + (child.enrollment ? ` (${child.enrollment})` : "");
            option.selected = String(child.id) === String(current || options[0].id);
            select.appendChild(option);
        });
        select.addEventListener("change", () => {
            const params = new URLSearchParams(window.location.search);
            params.set("student_id", select.value);
            window.location.search = params.toString();
        });
        overview.parentNode.insertBefore(wrapper, overview);
    }
    const dataNode = document.getElementById("parent-today-attendance");
    const card = document.querySelector(".parent-attendance-card");
    if (!dataNode || !card) return;
    let children;
    try { children = JSON.parse(dataNode.textContent || "[]"); } catch (_) { return; }
    const rows = children.map(child => `<div class="parent-today-attendance-item"><div><small>Student Name</small><strong>${child.name}</strong></div><div><small>Status</small><span class="parent-attendance-badge ${child.status.toLowerCase().replace(/\s+/g, '-')}">${child.status}</span><small class="parent-attendance-count">Attendance: ${child.present}/${child.total} lectures</small></div></div>`).join("");
    card.innerHTML = `<div class="card-icon green"><i class="fa-solid fa-calendar-check"></i></div><h3>Today's Attendance</h3>${rows || '<p class="parent-card-empty">No connected students.</p>'}`;
}, 0);
