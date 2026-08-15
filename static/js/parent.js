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
