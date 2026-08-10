// Get all role cards
const roles = document.querySelectorAll(".role");

// Get login title
const loginTitle = document.getElementById("loginTitle");
const loginRole = document.getElementById("loginRole");
const loginId = document.getElementById("loginId");

// Current selected role
let currentRole = "Student";

// Change selected role
function selectRole(element, roleName){

    // Remove active class from all cards
    roles.forEach(role=>{
        role.classList.remove("active");
    });

    // Add active class to clicked card
    element.classList.add("active");

    // Change login title
    loginTitle.innerText = roleName;

    // Save selected role
    currentRole = roleName.replace(" Login","");
    loginRole.value = currentRole;

    const identifierLabels = {
        Student: "Enrollment ID",
        Teacher: "Employee ID",
        Parent: "Parent ID",
        Admin: "Admin ID"
    };
    loginId.placeholder = identifierLabels[currentRole];
    loginId.value = "";
}
