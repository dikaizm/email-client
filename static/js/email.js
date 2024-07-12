
/**
 * GET /api/email/<int:email_id>
 * @param email_id 
 */
export default function viewEmail(email_id) {
    const emailView = document.getElementById('email-view');

    // GET /emails/<int:email_id>
    fetch(`/api/email/${email_id}`)
        .then(response => response.json())
        .then(email => {
            console.log(email);

            // Handle for error
            if (email.error) {
                emailView.innerHTML = `
                    <div class='alert alert-danger'>
                        ${email.error}
                    </div>
                `;
                return;
            }

            // Get cookie user email
            let user = getCookie('user_email')

            emailView.innerHTML = '';

            const encryptCondition = (email.data.encrypted || email.data.signed);

            let emailCard = renderEmailView(email.data,
                `
                    <strong>Message:</strong> <br>
                    <div class='d-flex flex-column gap-4 ${encryptCondition ? 'text-center' : ''}'>
                        ${encryptCondition ? (
                    `
                                    <p>
                                        ${email.data.sender_email} has sent you a protected message. Please click the button below to view the message.
                                    </p>
                                    <i class='fas fa-lock'></i>
                                    <div>
                                        <button type='button' id='btn-read-secured-email' class='btn btn-primary'>
                                            Read the message
                                        </button>
                                    </div>
                                `
                ) : `<p>${email.data.body}</p>`
                }
                    </div>
                `, `
                    ${email.data.encrypted ? `
                        <div class='badge bg-info'>
                            <i class='fas fa-lock'></i>
                            <span>Encrypted email</span>
                        </div>
                    ` : ''}
                `
            )

            emailView.appendChild(emailCard);

            // let archiveBtn = document.createElement('btn');
            // archiveBtn.className = `btn btn-warning my-2`;

            // archiveBtn.addEventListener('click', () => {
            //     archive_and_unarchive(email_id, email.data.archived);

            //     if (archiveBtn.innerText == 'Archive') {
            //         archiveBtn.innerText = 'Unarchive';
            //     } else {
            //         archiveBtn.innerText = 'Archive';
            //     }
            // });

            // if (!email.archived) {
            //     archiveBtn.innerHTML = `<i class='fas fa-folder-open'></i> Archive`;
            // } else {
            //     archiveBtn.innerHTML = `<i class='fas fa-folder'></i> Unarchive`;
            // }

            // emailView.appendChild(archiveBtn);

            // let replyBtn = document.createElement('btn');
            // replyBtn.className = `btn btn-success my-2`;
            // replyBtn.style.cssText = 'margin-left: 15px';
            // replyBtn.innerHTML = `<i class='fas fa-reply'></i> Reply`;
            // replyBtn.addEventListener('click', () => {
            //     reply(email.data.sender, email.data.subject, email.data.body, email.data.date);
            // });

            // emailView.appendChild(replyBtn);

            // Handle for read secured email
            let readSecuredMsgBtn = document.querySelector('#btn-read-secured-email');
            if (readSecuredMsgBtn) {
                readSecuredMsgBtn.addEventListener('click', () => handleReadSecuredMsg(email_id));
            }


            read(email_id);
        })
}


function getCookie(name) {
    const regex = new RegExp(`(^| )${name}=([^;]+)`)
    const match = document.cookie.match(regex)
    if (match) {
        const cleanedMatch = match[2].replace(/"/g, '')
        return cleanedMatch
    }
}


function renderEmailView(email, element, flag = null) {
    let div = document.createElement('div');
    div.className = `card my-1 items`;
    div.innerHTML = `
        <div class='card'>
            <div class='card-header'>
                <strong>${email.subject}</strong>
            </div>
            <div class='card-body' id='item-${email.id}'>
                <p class='card-title'>
                    <strong>From:</strong> <strong><span class='text-info'>${email.sender_email}</span></strong> &nbsp; |  &nbsp; <strong>To: </strong> <strong><span class='text-info'>${email.recipient_email}</span></strong> &nbsp; |  &nbsp; <strong>Date:</strong> ${email.date} 
                    <br>
                </p>
                <div class='card-text' id='email-message'>
                    ${element}
                </div>
                
                ${flag ? flag : ''}
                ${email.signed ? `
                    <div class='badge bg-success'>
                        <i class='fas fa-signature'></i>
                        <span>Signed email</span>
                    </div>
                ` : ''}
            </div>
        </div>
    `;

    return div;
}


/**
 * PUT /emails/<int:email_id>
 * @param email_id 
 */
function read(email_id) {
    // PUT /emails/<int:email_id>
    fetch(`/api/email/${email_id}`, {
        method: 'PUT',
        body: JSON.stringify({
            read: true
        })
    });
}

function handleReadSecuredMsg(email_id) {
    // Clear email view
    let emailView = document.getElementById('email-view');
    emailView.innerHTML = '';

    // Load passphrase input view
    emailView.appendChild(renderInputPassphrase());

    // Add event listener to submit passphrase
    let passphraseForm = document.querySelector('#form-input-passphrase');
    passphraseForm.addEventListener('submit', (event) => {
        event.preventDefault();

        handleSubmitPassphrase(email_id);
    })
}

function handleSubmitPassphrase(email_id) {
    let passphraseValue = document.querySelector('#email-secured-passphrase').value;

    if (!passphraseValue) {
        document.querySelector('#error-email-passphrase').textContent = 'Passphrase is required';
        return;
    }

    fetch(`/api/email/decrypt/${email_id}`, {
        method: 'POST',
        body: JSON.stringify({
            passphrase: passphraseValue
        })
    })
        .then(response => response.json())
        .then(result => {
            console.log(result);
            
            if (result.error) {
                console.error('Error decrypting message:', result.error);
                let errorDiv = document.querySelector('#error-email-passphrase');
                if (errorDiv.hasChildNodes()) {
                    errorDiv.innerHTML = '';
                }
                errorDiv.textContent = result.error;
                return;
            }

            const email = result.data;

            let emailCard = renderEmailView(email, `
                <strong>Message:</strong> <br>
                <div class='d-flex flex-column gap-4'>
                    <p>${email.body}</p>
                </div>
            `, `
                <div class='badge bg-info'>
                    <i class='fas fa-lock'></i>
                    <span>Encrypted email</span>
                </div>
            `);

            // Clear email view
            let emailView = document.getElementById('email-view');
            emailView.innerHTML = '';
            emailView.appendChild(emailCard);

            // let archiveBtn = document.createElement('btn');
            // archiveBtn.className = `btn btn-warning my-2`;

            // archiveBtn.addEventListener('click', () => {
            //     archive_and_unarchive(email_id, email.archived);

            //     if (archiveBtn.innerText == 'Archive') {
            //         archiveBtn.innerText = 'Unarchive';
            //     } else {
            //         archiveBtn.innerText = 'Archive';
            //     }
            // });

            // if (!email.archived) {
            //     archiveBtn.innerHTML = `<i class='fas fa-folder-open'></i> Archive`;
            // } else {
            //     archiveBtn.innerHTML = `<i class='fas fa-folder'></i> Unarchive`;
            // }

            // emailView.appendChild(archiveBtn);

            // let replyBtn = document.createElement('btn');
            // replyBtn.className = `btn btn-success my-2`;
            // replyBtn.style.cssText = 'margin-left: 15px';
            // replyBtn.innerHTML = `<i class='fas fa-reply'></i> Reply`;
            // replyBtn.addEventListener('click', () => {
            //     reply(email.sender, email.subject, email.body, email.timestamp);
            // });

            // emailView.appendChild(replyBtn);

            read(email_id);

        })
        .catch(error => {
            console.error('Error fetching decrypted message:', error);
            let errorDiv = document.querySelector('#error-email-passphrase');
            if (errorDiv.hasChildNodes()) {
                errorDiv.innerHTML = '';
            }
            errorDiv.textContent = error;
        });
}


function renderInputPassphrase() {
    let div = document.createElement('div');
    div.classList.add('h-half', 'd-flex', 'flex-column', 'justify-content-center');
    div.innerHTML = `
        <div class='mb-3'>
            <h3>Enter your passphrase to read the message</h3>
        </div>

        <form id='form-input-passphrase'>
            <id class='form-group row w-100 align-items-center'>
                <label for='email-secured-passphrase' class='col-sm-2 col-form-label d-flex align-items-center gap-2'>
                    <i class='fas fa-key'></i>
                    <span>Passphrase</span>
                </label>
                <div class='col-sm-8'>
                    <input type="password" id='email-secured-passphrase' class='form-control'>
                </div>

                <div class='col-sm-2'>
                    <button type='submit' id='btn-submit-passphrase' class='btn btn-primary'>Submit</button>
                </div>
            </id>
        </form>

        <div class='form-group row w-100'>
            <div class='col-sm-10 offset-sm-2'>
                <span id='error-email-passphrase' class='text-danger'></span>
            </div>
        </div>
    `;

    return div;
}