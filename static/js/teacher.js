// ===============================
// Teacher Dashboard Script
// EduSphere ERP
// ===============================

// Sidebar Active Menu

const menuItems = document.querySelectorAll(".sidebar ul li");

const teacherSidebar = document.querySelector(".sidebar ul");
if (teacherSidebar && !teacherSidebar.querySelector('[data-settings-link]') && !Array.from(teacherSidebar.children).some(item => item.textContent.trim() === "Settings")) {
    const settingsItem = document.createElement("li");
    settingsItem.setAttribute("data-settings-link", "true");
    settingsItem.innerHTML = '<i class="fa-solid fa-gear"></i><span>Settings</span>';
    settingsItem.addEventListener("click", () => { window.location.href = "/teacher/settings"; });
    const profile = teacherSidebar.querySelector(".sidebar-profile");
    const logout = Array.from(teacherSidebar.children).find(item => item.textContent.trim() === "Logout");
    teacherSidebar.insertBefore(settingsItem, profile || logout || null);
}
if (teacherSidebar && !teacherSidebar.querySelector('[data-teacher-schedule-link]') && !Array.from(teacherSidebar.children).some(item => item.textContent.trim() === "Manage Weekly Schedule")) {
    const scheduleItem = document.createElement("li");
    scheduleItem.setAttribute("data-teacher-schedule-link", "true");
    scheduleItem.innerHTML = '<i class="fa-solid fa-calendar-days"></i><span>Manage Weekly Schedule</span>';
    scheduleItem.addEventListener("click", () => { window.location.href = "/teacher/lectures"; });
    const materialsItem = Array.from(teacherSidebar.children).find(item => item.textContent.trim() === "Manage Materials");
    const logoutItem = Array.from(teacherSidebar.children).find(item => item.textContent.trim() === "Logout");
    teacherSidebar.insertBefore(scheduleItem, materialsItem || logoutItem || null);
}
if (teacherSidebar && !teacherSidebar.querySelector('[data-teacher-previous-attendance-link]') && !Array.from(teacherSidebar.children).some(item => item.textContent.trim() === "Previous Attendance")) {
    const previousAttendanceItem = document.createElement("li");
    previousAttendanceItem.setAttribute("data-teacher-previous-attendance-link", "true");
    previousAttendanceItem.innerHTML = '<i class="fa-solid fa-clock-rotate-left"></i><span>Previous Attendance</span>';
    previousAttendanceItem.addEventListener("click", () => { window.location.href = "/teacher/previous-attendance"; });
    const attendanceItem = Array.from(teacherSidebar.children).find(item => item.textContent.trim() === "Attendance");
    teacherSidebar.insertBefore(previousAttendanceItem, attendanceItem ? attendanceItem.nextSibling : null);
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
