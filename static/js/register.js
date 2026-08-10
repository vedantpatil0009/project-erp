// =====================================
// EduSphere ERP
// Register Page Script
// =====================================

const form = document.querySelector("form");
const roleSelect = document.getElementById("registrationRole");
const roleIdFields = document.querySelectorAll(".role-id-field");

function updateRoleIdField() {
    const selectedRole = roleSelect.value;

    roleIdFields.forEach(field => {
        const isSelectedRole = field.dataset.role === selectedRole;
        const input = field.querySelector("input");

        field.hidden = !isSelectedRole;
        input.disabled = !isSelectedRole;
        input.required = isSelectedRole;

        if (!isSelectedRole) {
            input.value = "";
        }
    });
}

roleSelect.addEventListener("change", updateRoleIdField);
updateRoleIdField();

form.addEventListener("submit", function(event){

    const password = document.querySelectorAll("input[type='password']")[0].value;

    const confirmPassword = document.querySelectorAll("input[type='password']")[1].value;

    if(password !== confirmPassword){

        alert("Passwords do not match!");

        event.preventDefault();

        

    }


});
