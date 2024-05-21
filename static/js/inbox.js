document.addEventListener('DOMContentLoaded', function () {

    // Use buttons to toggle between views
    document.querySelector('#inbox').addEventListener('click', () => load_mailbox('inbox'));
    document.querySelector('#sent').addEventListener('click', () => load_mailbox('sent'));
    document.querySelector('#archived').addEventListener('click', () => load_mailbox('archive'));
    document.querySelector('#security').addEventListener('click', load_security);
    document.querySelector('#compose').addEventListener('click', compose_email);
    document.querySelector('#compose-form').addEventListener('submit', send_email);

    // By default, load the inbox
    load_mailbox('inbox');
});


function compose_email() {
    // Show compose view and hide other views
    document.querySelector('#emails-view').style.display = 'none';
    document.querySelector('#security-view').style.display = 'none';
    document.querySelector('#compose-view').style.display = 'block';

    // Clear out composition fields
    document.querySelector('#compose-recipients').value = '';
    document.querySelector('#compose-subject').value = '';
    document.querySelector('#compose-body').value = '';
    document.querySelector('#compose-encrypt').checked = false;
}


/**
 * GET /security
 */
function load_security() {
    // Show the security view (PGP key pair and other user saved public key) and hide other views
    document.querySelector('#security-view').style.display = 'block';
    document.querySelector('#emails-view').style.display = 'none';
    document.querySelector('#compose-view').style.display = 'none';

    const pageView = document.querySelector('#security-view');

    // Page title
    const title = `
        <div>
            <h3>Security</h3>
            <p>PGP, or Pretty Good Privacy, is a system used for sending and receiving encrypted emails. A combination of public and private keys are used in PGP system to ensure secure end-to-end email communication.</p>
        </div>
    `;
    pageView.innerHTML = title;

    // My PGP key pair
    const myPgpKey = document.createElement('div')
    myPgpKey.style.marginTop = '2rem';
    myPgpKey.innerHTML = `
        <div>
            <h5>My Keys</h5>
            <div>
                <button type='button' class='btn btn-primary' id='btn-generate-key-form'>
                    <i class='fas fa-plus'></i> Generate a new key pair
                </button>
            </div>
            <table class='table table-hover table-dark mt-3'>
                <thead>
                    <tr>
                        <th scope="col">#</th>
                        <th scope="col">Public Key</th>
                        <th scope="col">Private Key</th>
                        <th scope="col">Expire</th>
                        <th scope="col">Created</th>
                        <th scope="col">Action</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <th scope="row">1</th>
                        <td>ankoaidjoajd-12kj1kkad</td>
                        <td>asdknahdojaojd0-donanod</td>
                        <td>12 July 2024</td>
                        <td>12 July 2021</td>
                        <td>
                            <a href='#' class='btn btn-danger'>
                                <i class='fas fa-trash'></i> Delete
                            </a>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;

    pageView.appendChild(myPgpKey);

    // Recipient saved public key
    const recipientPgpKey = document.createElement('div')
    recipientPgpKey.style.marginTop = '2rem';
    recipientPgpKey.innerHTML = `
        <div>
            <h5>Recipients' Keys</h5>
            <div>
                <button type='button' class='btn btn-primary' id='btn-import-recipient-key'>
                    <i class='fas fa-plus'></i> Import a public key
                </button>
            </div>
            <table class='table table-hover table-dark mt-3'>
                <thead>
                    <tr>
                        <th scope="col">#</th>
                        <th scope="col">User</th>
                        <th scope="col">Email</th>
                        <th scope="col">Public Key</th>
                        <th scope="col">Expire</th>
                        <th scope="col">Action</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <th scope="row">1</th>
                        <td>John Doe</td>
                        <td>john@mail.com</td>
                        <td>ankoaidjoajd-12kj1kkad</td>
                        <td>12 July 2024</td>
                        <td>
                            <a href='#' class='btn btn-danger'>
                                <i class='fas fa-trash'></i> Delete
                            </a>
                        </td>
                    </tr>
                    <tr>
                        <th scope="row">1</th>
                        <td>John Doe</td>
                        <td>john@mail.com</td>
                        <td>ankoaidjoajd-12kj1kkad</td>
                        <td>12 July 2024</td>
                        <td>
                            <a href='#' class='btn btn-danger'>
                                <i class='fas fa-trash'></i> Delete
                            </a>
                        </td>
                    </tr>
                    <tr>
                        <th scope="row">1</th>
                        <td>John Doe</td>
                        <td>john@mail.com</td>
                        <td>ankoaidjoajd-12kj1kkad</td>
                        <td>12 July 2024</td>
                        <td>
                            <a href='#' class='btn btn-danger'>
                                <i class='fas fa-trash'></i> Delete
                            </a>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    `

    pageView.appendChild(recipientPgpKey);

    // Button to show generate key pair form
    document.querySelector('#btn-generate-key-form').addEventListener('click', form_generate_key);
}


function form_generate_key() {
    const securityView = document.querySelector('#security-view')
    securityView.innerHTML = ''

    const div = document.createElement('div')
    div.innerHTML = `
        <h3 class='text-center mb-4'>Generate a new key pair</h3>
        <form id='generate-key-form'>
            <div class='form-group row mb-4'>
                <label for='generate-key-type' class='col-sm-2 col-form-label'>Key Type</label>
                <div class='col-sm-10'>
                    <select id='generate-key-type' class="form-select">
                        <option selected value='RSA'>RSA</option>
                        <option value="DSA">DSA</option>
                        <option value="ECDSA">ECDSA</option>
                    </select>
                </div>
            </div>
            <div class='form-group row mb-4'>
                <label for='generate-key-size' class='col-sm-2 col-form-label'>Key Size</label>
                <div class='col-sm-10'>
                    <input id='generate-key-size' class='form-control' value='2048'>
                    <span class='text-muted'>Example: 1024, 2048, 4096</span>
                </div>
            </div>
            <div class='form-group row mb-4'>
                <label for='generate-expiration' class='col-sm-2 col-form-label'>Expiration (days)</label>
                <div class='col-sm-10'>
                    <input id='generate-expiration' class='form-control'>
                    <span class='text-muted'>Example: 7, 14, 30, 365. Leave empty for no expiration</span>
                </div>
            </div>
            <div class='form-group row mb-4'>
                <label for='generate-passphrase' class='col-sm-2 col-form-label'>Passphrase</label>
                <div class='col-sm-10'>
                    <input id='generate-passphrase' class='form-control'>
                </div>
            </div>
            <div class='form-group row mb-4'>
                <label for='generate-comment' class='col-sm-2 col-form-label'>Comment</label>
                <div class='col-sm-10'>
                    <input id='generate-comment' class='form-control'>
                    <span class='text-muted'>Optional</span>
                </div>
            </div>

            <div class='form-group row'>
                <label class='col-sm-2'>
                </label>
                
                <div class='col-sm-10'>
                    <div class='d-grid gap-2'>
                        <input class='btn btn-primary mb-4' type='submit' value='Generate key'>
                    </div>
                </div>
            </div>
        </form>
    `

    securityView.appendChild(div)

    document.querySelector('#generate-key-form').addEventListener('submit', () => {
        console.log(document.querySelector('#generate-key-type').value);

        generate_key(
            document.querySelector('#generate-key-type').value,
            document.querySelector('#generate-key-size').value,
            document.querySelector('#generate-expiration').value,
            document.querySelector('#generate-passphrase').value,
            document.querySelector('#generate-comment').value
        )
    })
}


/**
 * POST /security/generate
 * @param key_type
 * @param key_size
 * @param key_expiration // optional
 * @param passphrase
 * @param comment // optional
 */
function generate_key(key_type, key_size, key_expiration, passphrase, comment) {
    event.preventDefault();

    // POST /security/generate
    fetch('/security/generate', {
        method: 'POST',
        body: JSON.stringify({
            key_type,
            key_size,
            comment,
            key_expiration,
            passphrase,
        })
    })
        .then(response => response.json())
        .then(result => {
            if (result.error) {
                const errorMsg = document.createElement('span')
                errorMsg.textContent = result.error
                document.querySelector('#error-generate-key').appendChild(errorMsg)
                return
            }

            localStorage.clear();
            load_security();
        })
}


/**
 * GET /emails/<str:mailbox>
 * @param mailbox 
 */
function load_mailbox(mailbox) {
    // Show the mailbox and hide other views
    document.querySelector('#emails-view').style.display = 'block';
    document.querySelector('#security-view').style.display = 'none';
    document.querySelector('#compose-view').style.display = 'none';

    // Show the mailbox name
    document.querySelector('#emails-view').innerHTML = `<h3>${mailbox.charAt(0).toUpperCase() + mailbox.slice(1)}</h3>`;

    // GET /emails/<str:mailbox>
    fetch(`/emails/${mailbox}`)
        .then(response => response.json())
        .then(emails => {
            console.log(emails);

            emails.forEach(email => {
                if (mailbox == 'inbox') {
                    if (email.read) {
                        is_read = 'read';
                    } else {
                        is_read = 'unread';
                    }
                } else {
                    is_read = 'unread';
                }

                let div = document.createElement('div');
                div.className = `card my-1 items`;
                if (email.body.length <= 99) {
                    div.innerHTML = `
                    <div class='card ${is_read}'>
                        <div class='card-header ${is_read}'>
                            <strong>${email.subject}</strong>
                        </div>
                        <div class='card-body ${is_read}' id='item-${email.id}'>
                            <p class='card-title'>
                                <strong>From:</strong> <strong>From:</strong> <strong><span class='text-info'>${email.sender}</span></strong> &nbsp; |  &nbsp; 
                                <strong>To:</strong> <strong>From:</strong> <strong><span class='text-info'>${email.recipients}</span></strong> &nbsp; |  &nbsp;  
                                <strong>Date:</strong> ${email.timestamp}
                            </p>
                            <p class='card-text'>
                                ${email.body.slice(0, 99)}
                            </p>
                            <a href='#' class='btn btn-primary'>
                                <i class='fas fa-book-reader'></i> Read
                            </a>
                        </div>
                    </div>
                `;
                } else {
                    div.innerHTML = `
                    <div class='card ${is_read}'>
                        <div class='card-header ${is_read}'>
                            <strong>${email.subject}</strong>
                        </div>
                        <div class='card-body ${is_read}' id='item-${email.id}'>
                            <p class='card-title'>
                                <strong>From:</strong> <strong><span class='text-info'>${email.sender}</span></strong> &nbsp; |  &nbsp;
                                <strong>To:</strong> <strong><span class='text-info'>${email.recipients}</span></strong> &nbsp; |  &nbsp;
                                <strong>Date:</strong> ${email.timestamp}
                            </p>
                            <p class='card-text'>
                                ${email.body.slice(0, 99)} <a href='#'>(more...)</a>
                            </p>
                            <a href='#' class='btn btn-primary'>
                                <i class='fas fa-book-reader'></i> Read
                            </a>
                        </div>
                    </div>
                `;
                }

                document.querySelector('#emails-view').appendChild(div);
                div.addEventListener('click', () => {
                    view_email(email.id, mailbox);
                });
            });
        })
}


/**
 * GET /emails/<int:email_id>
 * @param email_id 
 * @param mailbox 
 */
function view_email(email_id, mailbox) {
    // GET /emails/<int:email_id>
    fetch(`/emails/${email_id}`)
        .then(response => response.json())
        .then(email => {
            document.querySelector('#emails-view').innerHTML = '';

            let div = document.createElement('div');
            div.className = `card my-1 items`;
            div.innerHTML = `
            <div class='card'>
                <div class='card-header'>
                    <strong>${email.subject}</strong>
                </div>
                <div class='card-body' id='item-${email.id}'>
                    <p class='card-title'>
                        <strong>From:</strong> <strong><span class='text-info'>${email.sender}</span></strong> &nbsp; |  &nbsp; <strong>To: </strong> <strong><span class='text-info'>${email.recipients}</span></strong> &nbsp; |  &nbsp; <strong>Date:</strong> ${email.timestamp} 
                        <br>
                    </p>
                    <div class='card-text'>
                        <strong>Message:</strong> <br>
                        <div class='text-center d-flex flex-column gap-4'>
                            ${(email.encrypted) ? (
                    `
                                        <p>
                                            ${email.sender} has sent you a protected message. Please click the button below to view the message.
                                        </p>
                                        <i class='fas fa-lock'></i>
                                        <div>
                                            <a href='#' class='btn btn-primary'>
                                                Read the message
                                            </a>
                                        </div>
                                    `
                ) : `<p>${email.body}</p>`
                }
                        </div>
                    </div>
                </div>
            </div>
        `;

            document.querySelector('#emails-view').appendChild(div);
            if (mailbox == 'sent') return;

            let archiveBtn = document.createElement('btn');
            archiveBtn.className = `btn btn-warning my-2`;

            archiveBtn.addEventListener('click', () => {
                archive_and_unarchive(email_id, email.archived);

                if (archiveBtn.innerText == 'Archive') {
                    archiveBtn.innerText = 'Unarchive';
                } else {
                    archiveBtn.innerText = 'Archive';
                }
            });

            if (!email.archived) {
                archiveBtn.innerHTML = `<i class='fas fa-folder-open'></i> Archive`;
            } else {
                archiveBtn.innerHTML = `<i class='fas fa-folder'></i> Unarchive`;
            }

            document.querySelector('#emails-view').appendChild(archiveBtn);

            let replyBtn = document.createElement('btn');
            replyBtn.className = `btn btn-success my-2`;
            replyBtn.style.cssText = 'margin-left: 15px';
            replyBtn.innerHTML = `<i class='fas fa-reply'></i> Reply`;
            replyBtn.addEventListener('click', () => {
                reply(email.sender, email.subject, email.body, email.timestamp);
            });

            document.querySelector('#emails-view').appendChild(replyBtn);
            read(email_id);
        })
}


/**
 * POST /emails
 */
function send_email() {
    event.preventDefault();

    // POST /emails
    fetch('/emails', {
        method: 'POST',
        body: JSON.stringify({
            recipients: document.querySelector('#compose-recipients').value,
            subject: document.querySelector('#compose-subject').value,
            body: document.querySelector('#compose-body').value,
            encrypt: document.querySelector('#compose-encrypt').checked
        })
    })
        .then(response => response.json())
        .then(result => {
            if (result.error) {
                const errorMsg = document.createElement('span')
                errorMsg.textContent = result.error
                document.querySelector('#compose-to-error').appendChild(errorMsg)
                return
            }

            localStorage.clear();
            load_mailbox('sent');
        })
}


/**
 * PUT /emails/<int:email_id>
 * @param email_id 
 * @param state 
 */
function archive_and_unarchive(email_id, state) {
    // PUT /emails/<int:email_id>
    fetch(`/emails/${email_id}`, {
        method: 'PUT',
        body: JSON.stringify({
            archived: !state
        })
    })
        .then(response => load_mailbox('inbox'));
}


/** 
 * @param sender 
 * @param subject 
 * @param body 
 * @param timestamp 
 */
function reply(sender, subject, body, timestamp) {
    compose_email();

    if (!/^Re:/.test(subject)) {
        subject = `Re: ${subject}`;
    }

    document.querySelector('#compose-recipients').value = sender;
    document.querySelector('#compose-subject').value = subject;

    pre_fill = `On ${timestamp} ${sender} wrote:\n${body}\n`;

    document.querySelector('#compose-body').value = pre_fill;
}


/**
 * PUT /emails/<int:email_id>
 * @param email_id 
 */
function read(email_id) {
    // PUT /emails/<int:email_id>
    fetch(`/emails/${email_id}`, {
        method: 'PUT',
        body: JSON.stringify({
            read: true
        })
    });
}