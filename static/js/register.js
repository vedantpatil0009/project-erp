// =====================================
// EduSphere ERP
// Register Page Script
// =====================================

const form = document.querySelector("form");
const roleSelect = document.getElementById("registrationRole");
const roleIdFields = document.querySelectorAll(".role-id-field");
const departmentField = document.querySelector(".department-field");
const departmentSelect = document.getElementById("registrationDepartment");
const parentEmailField = document.querySelector(".parent-email-field");
const parentEmailInput = document.getElementById("registrationParentEmail");

function updateRoleIdField() {
    const selectedRole = roleSelect.value;
    const departmentRequired = selectedRole === "Student" || selectedRole === "Teacher";

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

    departmentField.hidden = !departmentRequired;
    departmentSelect.disabled = !departmentRequired;
    departmentSelect.required = departmentRequired;

    if (!departmentRequired) {
        departmentSelect.value = "";
    }

    const parentEmailRequired = selectedRole === "Student";
    parentEmailField.hidden = !parentEmailRequired;
    parentEmailInput.disabled = !parentEmailRequired;
    parentEmailInput.required = parentEmailRequired;

    if (!parentEmailRequired) {
        parentEmailInput.value = "";
    }
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
