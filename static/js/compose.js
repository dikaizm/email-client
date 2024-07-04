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

        console.log(hasPublicKey);

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

    composeRecipients.addEventListener('change', debouncedInputHandler);
});


/**
 * Compose an email
 */