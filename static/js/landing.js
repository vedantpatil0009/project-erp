// Mobile menu placeholder
const menu = document.getElementById("menu");

menu.addEventListener("click", () => {
    alert("Mobile menu will be added in the complete version.");
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener("click", function(e) {
        e.preventDefault();

        document.querySelector(this.getAttribute("href")).scrollIntoView({
            behavior: "smooth"
        });
    });
});