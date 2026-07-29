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