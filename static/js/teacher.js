// ===============================
// Teacher Dashboard Script
// EduSphere ERP
// ===============================

// Sidebar Active Menu

const menuItems = document.querySelectorAll(".sidebar ul li");

menuItems.forEach(item => {

    item.addEventListener("click", () => {

        menuItems.forEach(i => i.classList.remove("active"));

        item.classList.add("active");

    });

});

// Card Hover Animation

const cards = document.querySelectorAll(".card");

cards.forEach(card => {

    card.addEventListener("mouseenter", () => {

        card.style.transform = "translateY(-8px) scale(1.03)";

    });

    card.addEventListener("mouseleave", () => {

        card.style.transform = "translateY(0) scale(1)";

    });

});

// Graph Animation

const bars = document.querySelectorAll(".bar");

bars.forEach(bar => {

    const finalHeight = bar.style.height;

    bar.style.height = "0";

    setTimeout(() => {

        bar.style.height = finalHeight;

    },300);

});

// Quick Action Buttons

const buttons = document.querySelectorAll("button");

buttons.forEach(button => {

    button.addEventListener("click", function(){

        const text = this.innerText;

        if(text === "Mark Attendance"){
            alert("Attendance page will open.");
        }

        else if(text === "Upload Assignment"){
            alert("Assignment upload page will open.");
        }

        else if(text === "Upload Notes"){
            alert("Study material upload page will open.");
        }

        else if(text === "Enter Marks"){
            alert("Marks entry page will open.");
        }

        else{
            alert("Feature coming soon.");
        }

    });

});

// Assignment Upload Form

const form = document.querySelector("form");

if(form){

    form.addEventListener("submit", function(e){

        e.preventDefault();

        alert("Assignment Uploaded Successfully!");

        form.reset();

    });

}

// Student Table Hover

const rows = document.querySelectorAll("table tr");

rows.forEach((row,index)=>{

    if(index !== 0){

        row.addEventListener("mouseenter",()=>{

            row.style.background="#e6fffb";

        });

        row.addEventListener("mouseleave",()=>{

            row.style.background="";

        });

    }

});

// Welcome Message

window.onload = () => {

    console.log("Welcome to EduSphere Teacher Dashboard");

};