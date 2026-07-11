// ===================================
// EduSphere Parent Dashboard
// script.js
// ===================================

// Sidebar Active Menu

const menuItems = document.querySelectorAll(".sidebar ul li");

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