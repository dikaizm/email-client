document.addEventListener('DOMContentLoaded', function () {
    // Get csrf token
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    const emailField = document.getElementById('email');

    function debounce(func, wait) {
        let timeout;
        return function (...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    async function validateEmail(event) {

        const value = event.target.value;
        // Check if the email is valid
        if (value.includes('@') && value.includes('.')) {
            emailField.classList.remove('is-invalid');
            emailField.classList.add('is-valid');

            // Check if the email is already registered
            const isEmailRegistered = await checkEmailOnServer();

            // Show password fields
            showPasswordFields(isEmailRegistered);

        } else {
            emailField.classList.remove('is-valid');
            emailField.classList.add('is-invalid');

            // Clear password fields
            const passwordWrapper = document.getElementById('password-wrapper');
            passwordWrapper.innerHTML = '';
        }
    }

    async function checkEmailOnServer() {
        return await fetch('/api/auth/email-validation', {
            method: 'POST',
            body: JSON.stringify({ email: emailField.value }),
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            }
        })
            .then(response => response.json())
            .then(data => {
                return data.data.is_registered; // Return the result from the server
            })
            .catch(error => {
                console.error('Error checking email on server:', error);
                return false; // Handle errors gracefully
            });
    }

    function showPasswordFields(isRegistered) {
        const passwordWrapper = document.getElementById('password-wrapper');
        passwordWrapper.innerHTML = ''; // Clear any existing fields

        function createPasswordField(id, placeholder) {
            const field = document.createElement('input');
            field.type = 'password';
            field.id = id;
            field.name = id;
            field.placeholder = placeholder;
            field.classList.add('form-control');
            passwordWrapper.appendChild(field);
        }

        createPasswordField('password', 'Password');

        if (!isRegistered) {
            createPasswordField('confirm-password', 'Confirm Password');
        }
    }

    emailField.addEventListener('input', debounce(validateEmail, 500)); // 300 ms debounce time
});
