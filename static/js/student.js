// Sidebar Menu Active State

const menuItems = document.querySelectorAll(".sidebar ul li");

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

    console.log("Welcome to EduSphere Student Dashboard");

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