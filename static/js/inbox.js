import viewEmail from './email.js';

document.addEventListener('DOMContentLoaded', async function () {
    const emailsList = document.getElementById('emails-list');

    const emails = await fetchEmails();
    if (!emails.success) {
        // Display error message
        const div = document.createElement('div');
        div.className = 'alert alert-danger';
        div.innerHTML = 'Error fetching emails. Please try again later.';
        emailsList.appendChild(div);
    } else if (emails.data.length === 0) {
        // Display no emails message
        const div = document.createElement('div');
        div.className = 'alert alert-info';
        div.innerHTML = 'No emails to display.';
        emailsList.appendChild(div);
    } else {
        displayEmails(emails.data);
    }

    const btnRefreshInbox = document.getElementById('btn-refresh-inbox');
    btnRefreshInbox.addEventListener('click', async function () {
        console.log('Refreshing inbox');

        // Disable button
        btnRefreshInbox.setAttribute('disabled', 'disabled');
        // Rotate refresh icon
        const refreshIcon = document.getElementById('refresh-icon');
        if (refreshIcon) {
            refreshIcon.innerHTML = `
                <div class="spinner-border text-info" role="status" style="height: 20px; width: 20px;">
                    <span class="sr-only">Loading...</span>
                </div>
            `
        }

        const refreshedEmails = await refreshEmails();
        if (!refreshedEmails.success) {
            btnRefreshInbox.removeAttribute('disabled');
            btnRefreshInbox.innerHTML = `<i class="bi bi-arrow-clockwise"></i>`;

            // Display error message
            const div = document.createElement('div');
            div.className = 'alert alert-danger';
            div.innerHTML = 'Error fetching emails. Please try again later.';
            emailsList.appendChild(div);
        } else {
            window.location.reload();
        }
    })
});

async function fetchEmails() {
    try {
        const response = await fetch('/api/email/inbox', {
            method: 'GET'
        })
        const emails = await response.json();
        console.log(emails);
        return emails;
    } catch (error) {
        console.error('Error fetching emails:', error);
        return null;
    }
}

async function refreshEmails() {
    try {
        const response = await fetch('/api/email/refresh/INBOX', {
            method: 'GET'
        })
        const emails = await response.json();
        console.log(emails);
        return emails;
    } catch (error) {
        console.error('Error fetching emails:', error);
        return null;
    }
}

function displayEmails(data) {
    let is_read = '';

    data.emails.forEach(email => {
        if (email.read) {
            is_read = 'read';
        } else {
            is_read = 'unread';
        }

        const encryptCondition = email.encrypted && (email.recipients != data.user);

        const emailBody = email.body.length >= 99 ? `${email.body.slice(0, 99)} <a href='#'>(more...)</a>` : email.body.slice(0, 99);

        let emailCard = document.createElement('div');
        emailCard.className = `card my-1 items`;
        emailCard.innerHTML = `
                    <div class='card ${is_read}'>
                        <div class='card-header ${is_read}'>
                            <strong>${email.subject}</strong>
                        </div>
                        <div class='card-body ${is_read}' id='item-${email.id}'>
                            <p class='card-title'>
                                <strong>From:</strong> <strong><span class='text-info'>${email.sender_email}</span></strong> &nbsp; |  &nbsp;
                                <strong>To:</strong> <strong><span class='text-info'>${email.recipient_email}</span></strong> &nbsp; |  &nbsp;
                                <strong>Date:</strong> ${email.date}
                            </p>
                            <p class='card-text'>
                                ${encryptCondition ? (emailBody) : (email.encrypted ? `
                                <i class='fas fa-lock'></i> Encrypted message
                            ` : (emailBody))}
                            </p>
                            <a href='#' class='btn btn-primary'>
                                <i class='fas fa-book-reader'></i> Read
                            </a>
                        </div>
                    </div>
                `;

        document.getElementById('inbox-view').appendChild(emailCard);

        emailCard.addEventListener('click', () => {
            document.getElementById('inbox-view').innerHTML = '';
            viewEmail(email.id);
        });
    })
}