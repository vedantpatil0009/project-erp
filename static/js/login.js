// Get all role cards
const roles = document.querySelectorAll(".role");

// Get login title
const loginTitle = document.getElementById("loginTitle");

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
}

// Login Button
const form = document.querySelector("form");

form.addEventListener("submit",function(e){

    e.preventDefault();

    alert(currentRole + " Login Successful!");

    // Redirect according to role
    if(currentRole === "Student"){
        window.location.href = "/student";
    }

    else if(currentRole === "Teacher"){
        window.location.href = "/teacher";
    }

    else if(currentRole === "Parent"){
        window.location.href = "/parent";
    }

    else if(currentRole === "Admin"){
        window.location.href = "/admin";
    }

});