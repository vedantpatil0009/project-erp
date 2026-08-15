// =======================================
// EduSphere ERP
// Admin Dashboard Script
// =======================================

// Sidebar Active Menu

const menuItems = document.querySelectorAll(".sidebar ul li");
const adminSidebar = document.querySelector(".sidebar ul");
if (adminSidebar && !adminSidebar.querySelector('[data-settings-link]')) {
    const settingsItem = document.createElement("li");
    settingsItem.setAttribute("data-settings-link", "true");
    settingsItem.innerHTML = '<i class="fa-solid fa-gear"></i><span>Settings</span>';
    settingsItem.addEventListener("click", () => { window.location.href = "/admin/settings"; });
    const profile = adminSidebar.querySelector(".sidebar-profile");
    const logout = Array.from(adminSidebar.children).find(item => item.textContent.trim() === "Logout");
    adminSidebar.insertBefore(settingsItem, profile || logout || null);
}
const profileItem = document.querySelector(".sidebar-profile");
if (profileItem && !profileItem.getAttribute("onclick")) {
    profileItem.addEventListener("click", () => {
        window.location.href = "/admin/profile";
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

    console.log("Welcome Admin!");

};
