/**
 * Check if the recipient has a public key
 */
document.addEventListener('DOMContentLoaded', function () {
    const composeRecipients = document.getElementById('compose-recipients');

    async function isRecipientHasPublicKey(recipient) {
        try {
            const response = await fetch('/api/email/find-pubkey/' + recipient, {
                method: 'GET',
            });

            const data = await response.json();
            return data; // Return the fetched data
        } catch (error) {
            console.error('Error fetching public key:', error);
            return { success: false }; // Return false for any errors
        }
    }

    // Debounce function
    function debounce(func, wait) {
        let timeout;
        return function (...args) {
            const context = this;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), wait);
        };
    }

    // Debounced input event handler
    const debouncedInputHandler = debounce(async function () {
        const recipients = composeRecipients.value.split(',');
        const recipient = recipients[recipients.length - 1].trim();

        if (recipient.length === 0) {
            return;
        }

        const hasPublicKey = await isRecipientHasPublicKey(recipient);

        const recipientMsg = document.getElementById('recipient-msg');
        recipientMsg.innerHTML = '';
        recipientMsg.classList.remove('text-success', 'text-danger');

        if (hasPublicKey.success) {
            recipientMsg.innerHTML = hasPublicKey.message;
            recipientMsg.classList.add('text-success');
        } else {
            recipientMsg.innerHTML = hasPublicKey.error;
            recipientMsg.classList.add('text-danger');
        }
    }, 2000); // 2000ms debounce

    composeRecipients.addEventListener('change', () => {
        const isEncrypt = document.getElementById('compose-encrypt').checked;
        const isSign = document.getElementById('compose-sign').checked;

        if (isEncrypt || isSign) {
            debouncedInputHandler();
        }
    });
});


/**
 * Compose an email
 */
document.addEventListener('DOMContentLoaded', function () {

    async function sendEmail(event) {
        event.preventDefault();

        const btnSend = document.getElementById('compose-send');
        btnSend.setAttribute('disabled', 'disabled');
        btnSend.innerHTML = `
            <div class="spinner-border text-info" role="status" style="height: 20px; width: 20px;">
                <span class="sr-only">Loading...</span>
            </div>
        `;

        const recipients = document.getElementById('compose-recipients').value;
        const subject = document.getElementById('compose-subject').value;
        const body = document.getElementById('compose-body').value;
        const isEncrypt = document.getElementById('compose-encrypt').checked;
        const isSign = document.getElementById('compose-sign').checked;
        const passphrase = document.getElementById('compose-passphrase') ? document.getElementById('compose-passphrase').value : '';

        const emailData = {
            recipients: recipients,
            subject: subject,
            body: body,
            encrypt: isEncrypt,
            sign: isSign,
            passphrase: passphrase
        };

        try {
            const response = await fetch('/api/email/send', {
                method: 'POST',
                body: JSON.stringify(emailData),
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            console.log(data);

            if (!data.success) {
                btnSend.removeAttribute('disabled');
                btnSend.innerHTML = 'Send';
                return showError(data.error);
            }

            // Load the sent emails
            window.location.href = '/sent';

        } catch (error) {
            console.error('Error sending email:', error);

            btnSend.removeAttribute('disabled');
            btnSend.innerHTML = 'Send';
            return showError('Error sending email. Please try again later.');
        }
    }

    const signCheckbox = document.getElementById('compose-sign');
    if (signCheckbox) {
        signCheckbox.addEventListener('change', function () {
            const passphraseWrapper = document.getElementById('passphrase-input');

            const passphraseInput = document.createElement('input');
            passphraseInput.type = 'password';
            passphraseInput.id = 'compose-passphrase';
            passphraseInput.className = 'form-control';
            passphraseInput.placeholder = 'Your key passphrase';

            passphraseInput.addEventListener('input', function () {
                const composeError = document.getElementById('compose-error');
                composeError.innerHTML = '';
            })

            if (document.querySelector('#compose-sign').checked) {
                passphraseWrapper.appendChild(passphraseInput);
            } else {
                passphraseWrapper.innerHTML = '';
            }
        });
    }

    const composeForm = document.getElementById('compose-form');
    if (composeForm) {
        composeForm.addEventListener('submit', (event) => sendEmail(event));
    }
})


function showError(message) {
    const composeError = document.getElementById('compose-error');
    composeError.innerHTML = '';

    const alert = document.createElement('div');
    alert.className = 'alert alert-danger';
    alert.innerHTML = message;
    return composeError.appendChild(alert);
}