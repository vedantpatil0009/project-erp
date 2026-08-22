// Sidebar Menu Active State

const menuItems = document.querySelectorAll(".sidebar ul li");

const studentSidebar = document.querySelector(".sidebar ul");
if (studentSidebar && !studentSidebar.querySelector('[data-final-result-link]') && !Array.from(studentSidebar.children).some(item => item.textContent.trim() === "Final Result")) {
    const finalResultItem = document.createElement("li");
    finalResultItem.setAttribute("data-final-result-link", "true");
    finalResultItem.innerHTML = '<i class="fa-solid fa-file-certificate"></i><span>Final Result</span>';
    finalResultItem.addEventListener("click", () => { window.location.href = "/student/final-results"; });
    const settingsItem = Array.from(studentSidebar.children).find(item => item.textContent.trim() === "Settings");
    studentSidebar.insertBefore(finalResultItem, settingsItem || null);
}

menuItems.forEach(item => {
    item.addEventListener("click", () => {

        menuItems.forEach(i => i.classList.remove("active"));

        item.classList.add("active");

    });
});

// Dashboard Card Hover Animation

const cards = document.querySelectorAll(".card");

cards.forEach(card => {

    card.addEventListener("mouseenter", () => {

        card.style.transform = "translateY(-8px) scale(1.03)";

    });

    card.addEventListener("mouseleave", () => {

        card.style.transform = "translateY(0) scale(1)";

    });

});

// Download Button

const buttons = document.querySelectorAll("button");

buttons.forEach(button => {

    button.addEventListener("click", () => {

        alert("Download feature will be connected with backend.");

    });

});

// Welcome Message

window.onload = () => {

    console.log("Welcome to Educon Student Dashboard");

};

// Graph Animation

const bars = document.querySelectorAll(".bar");

bars.forEach((bar) => {

    const height = bar.style.height;

    bar.style.height = "0";

    setTimeout(() => {

        bar.style.height = height;

    },300);

});
