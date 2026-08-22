const menu = document.getElementById("menu");
const mobileMenu = document.getElementById("mobile-menu-panel");
const mobileMenuIcon = menu ? menu.querySelector("i") : null;

if (menu && mobileMenu) {
    menu.addEventListener("click", () => {
        const isOpen = mobileMenu.classList.toggle("open");
        mobileMenu.setAttribute("aria-hidden", String(!isOpen));
        menu.setAttribute("aria-expanded", String(isOpen));
        if (mobileMenuIcon) {
            mobileMenuIcon.classList.toggle("fa-bars", !isOpen);
            mobileMenuIcon.classList.toggle("fa-xmark", isOpen);
        }
    });

    mobileMenu.querySelectorAll("a").forEach(link => {
        link.addEventListener("click", () => {
            mobileMenu.classList.remove("open");
            mobileMenu.setAttribute("aria-hidden", "true");
            menu.setAttribute("aria-expanded", "false");
            if (mobileMenuIcon) {
                mobileMenuIcon.classList.add("fa-bars");
                mobileMenuIcon.classList.remove("fa-xmark");
            }
        });
    });

    window.addEventListener("resize", () => {
        if (window.innerWidth > 800) {
            mobileMenu.classList.remove("open");
            mobileMenu.setAttribute("aria-hidden", "true");
            menu.setAttribute("aria-expanded", "false");
            if (mobileMenuIcon) {
                mobileMenuIcon.classList.add("fa-bars");
                mobileMenuIcon.classList.remove("fa-xmark");
            }
        }
    });
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener("click", function(e) {
        e.preventDefault();

        document.querySelector(this.getAttribute("href")).scrollIntoView({
            behavior: "smooth"
        });
    });
});

const slides = document.querySelectorAll(".slide");
const dots = document.querySelectorAll(".dot");

let current = 0;

function showSlide(index){

    slides[current].classList.remove("active");
    dots[current].classList.remove("active");

    current = index;

    slides[current].classList.add("active");
    dots[current].classList.add("active");

}

// Automatic slideshow
setInterval(function(){

    let next = current + 1;

    if(next >= slides.length){
        next = 0;
    }

    showSlide(next);

},3000);

// Click on dots
for(let i = 0; i < dots.length; i++){

    dots[i].onclick = function(){

        showSlide(i);

    };

}
