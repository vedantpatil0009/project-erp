// ===============================
// Teacher Dashboard Script
// EduSphere ERP
// ===============================

// Sidebar Active Menu

const menuItems = document.querySelectorAll(".sidebar ul li");

const teacherSidebar = document.querySelector(".sidebar ul");
if (teacherSidebar && !teacherSidebar.querySelector('[data-teacher-schedule-link]')) {
    const scheduleItem = document.createElement("li");
    scheduleItem.setAttribute("data-teacher-schedule-link", "true");
    scheduleItem.innerHTML = '<i class="fa-solid fa-calendar-days"></i><span>Manage Weekly Schedule</span>';
    scheduleItem.addEventListener("click", () => { window.location.href = "/teacher/lectures"; });
    const materialsItem = Array.from(teacherSidebar.children).find(item => item.textContent.trim() === "Manage Materials");
    const logoutItem = Array.from(teacherSidebar.children).find(item => item.textContent.trim() === "Logout");
    teacherSidebar.insertBefore(scheduleItem, materialsItem || logoutItem || null);
}

const lectureHeading = document.querySelector(".teacher-lectures .section-heading");
if (lectureHeading && !lectureHeading.querySelector(".edit-lectures-link")) {
    const link = document.createElement("a");
    link.className = "profile-button edit-lectures-link";
    link.href = "/teacher/lectures";
    link.textContent = "Edit Lectures";
    lectureHeading.insertBefore(link, lectureHeading.lastElementChild);
}

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

            row.style.background="#B0E0E6";

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
