// =====================================
// EduSphere ERP
// Register Page Script
// =====================================

const form = document.querySelector("form");

form.addEventListener("submit", function(event){

    const password = document.querySelectorAll("input[type='password']")[0].value;

    const confirmPassword = document.querySelectorAll("input[type='password']")[1].value;

    if(password !== confirmPassword){

        alert("Passwords do not match!");

        event.preventDefault();

        

    }


});