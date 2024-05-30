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
    document.querySelector('#compose-sign').checked = false;

    // Show passphrase input if sign is checked
    document.querySelector('#compose-sign').addEventListener('change', () => {
        const passphraseInput = document.querySelector('#passphrase-input');
        const passphraseInner = `
            <input type='password' id='compose-passphrase' class='form-control' placeholder='Your key passphrase'>
        `

        if (document.querySelector('#compose-sign').checked) {
            passphraseInput.innerHTML = passphraseInner;
        } else {
            passphraseInput.innerHTML = '';
        }
    });
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

    const myPgpKeyHeader = document.createElement('div')
    myPgpKeyHeader.innerHTML = `
        <h5>My Keys</h5>
        <div>
            <button type='button' class='btn btn-primary' id='btn-generate-key-form'>
                <i class='fas fa-plus'></i> Generate a new key pair
            </button>
        </div>
    `

    myPgpKey.appendChild(myPgpKeyHeader)

    // GET /security/keys
    fetch('/api/security/keys', {
        method: 'GET',
    })
        .then(response => response.json())
        .then(result => {
            if (result.error) {
                const errorMsg = document.createElement('span')
                errorMsg.textContent = result.error
                myPgpKey.appendChild(errorMsg)
                return
            }

            const myPgpKeyTable = document.createElement('div')
            myPgpKeyTable.innerHTML = `
                <table class='table table-hover table-dark mt-3'>
                    <thead>
                        <tr>
                            <th scope="col">#</th>
                            <th scope="col">Key ID</th>
                            <th scope="col">Expire</th>
                            <th scope="col">Encrypt</th>
                            <th scope="col">Sign</th>
                            <th scope="col">Key Size</th>
                            <th scope="col">Created</th>
                            <th scope="col">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${user_keys_table(result)}
                    </tbody>
                </table>
            `;

            myPgpKey.appendChild(myPgpKeyTable);
            click_user_key_item();
        });

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


function click_user_key_item() {
    document.querySelectorAll('.btn-user-key-detail').forEach(button => {
        button.addEventListener('click', function () {
            const keyId = this.getAttribute('data-key-id');
            fetch(`/api/security/keys/${keyId}`)
                .then(response => response.json())
                .then(data => {
                    user_key_detail(data);
                })
                .catch(error => {
                    console.error('Error fetching key details:', error);
                });
        });
    });

    document.querySelectorAll('.btn-user-key-delete').forEach(button => {
        button.addEventListener('click', function () {
            const keyId = this.getAttribute('data-key-id');
            fetch(`/api/security/keys/${keyId}`, { method: 'DELETE' })
                .then(response => {
                    if (response.ok) {
                        const securityView = document.querySelector('#security-view');
                        securityView.innerHTML = '';
                        load_security();
                    } else {
                        console.error('Failed to delete key');
                    }
                })
                .catch(error => {
                    console.error('Error deleting key:', error);
                });
        });
    });
}


function user_keys_table(data) {
    const tableRows = data.map((item, index) => {
        return `
            <tr>
                <th scope="row">${index + 1}</th>
                <td class="w-30 text-break">
                    ${item.default_key ?
                `<span class='badge bg-primary'>Default</span>`
                : ``
            }
                    <p>${item.key_id}</p>
                </td>
                <td>${item.expire_date}</td>
                <td><span class='badge ${item.encrypt ? 'bg-success' : 'bg-danger'}'>${capitalize_first_letter(`${item.encrypt}`)}</span></td>
                <td><span class='badge ${item.sign ? 'bg-success' : 'bg-danger'}'>${capitalize_first_letter(`${item.sign}`)}</span></td>
                <td>${item.key_size}</td>
                <td>${item.created}</td>
                <td>
                    <button type='button' class='btn btn-primary btn-user-key-detail' data-key-id='${item.key_id}' title='detail'>
                        <i class='fas fa-eye'></i>
                    </button>
                    <button type='button' class='btn btn-danger btn-user-key-delete' data-key-id='${item.key_id}' title='delete'>
                        <i class='fas fa-trash'></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');

    return tableRows
}


/**
 * 
 * @param data {key_id, private_key, public_key, expire_date, encrypt, sign, key_size, passphrase, default_key, created}
 */
function user_key_detail(data) {
    const securityView = document.querySelector('#security-view');
    securityView.innerHTML = '';

    function key_mapper(key) {
        const keyMap = {
            'key_id': 'Key ID',
            'private_key': 'Private Key',
            'public_key': 'Public Key',
            'expire_date': 'Expire Date',
            'encrypt': 'Encrypt',
            'sign': 'Sign',
            'key_size': 'Key Size',
            'passphrase': 'Passphrase',
            'default_key': 'Default Key',
            'created': 'Created'
        };

        return keyMap[key] || key;
    }

    function key_detail_rows() {
        objToArr = Object.entries(data).map(([key, value]) => {
            return { key: key, value: value }
        })

        return objToArr.map(item => {
            return `
                <tr>
                    <td scope="row">${key_mapper(item.key)}</td>
                    <td>${item.value}</td>
                </tr>
            `;
        }).join('');
    }

    const div = document.createElement('div')
    div.innerHTML = `
        <h3 class='mb-4'>Key Details</h3>
        <table class="table table-sm">
            <thead>
                <tr>
                    <th scope="col">Description</th>
                    <th scope="col">Value</th>
                </tr>
            </thead>
            <tbody>
                ${key_detail_rows()}
            </tbody>
        </table>
    `;

    securityView.appendChild(div);
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
                    </select>
                </div>
            </div>
            <div class='form-group row mb-4'>
                <label for='generate-key-size' class='col-sm-2 col-form-label'>Key Size</label>
                <div class='col-sm-10'>
                    <input id='generate-key-size' class='form-control' value='2048'>
                    <span id='rsa-dsa-key-size-hint' class='text-muted'>Key size: 1024, 2048, 4096</span>
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
                        <input class='btn btn-primary' type='submit' value='Generate key'>
                        <span id='error-generate-key' class='text-danger'></span>
                    </div>
                </div>
            </div>
        </form>
    `

    securityView.appendChild(div)

    document.querySelector('#generate-key-form').addEventListener('submit', () => {
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
    fetch('/api/security/generate', {
        method: 'POST',
        body: JSON.stringify({
            key_type,
            key_size: parseInt(key_size),
            comment,
            expire: parseInt(key_expiration),
            passphrase,
        })
    })
        .then(response => response.json())
        .then(result => {
            if (result.error) {
                if (document.querySelector('#error-generate-key').hasChildNodes()) {
                    document.querySelector('#error-generate-key').innerHTML = '';
                }

                const errorMsg = document.createElement('span')
                errorMsg.textContent = result.error
                document.querySelector('#error-generate-key').appendChild(errorMsg)
                return
            }

            localStorage.clear();
            document.querySelector('#security-view').innerHTML = '';
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
            const user = getCookie('user_email')

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

                const encryptCondition = email.encrypted && (email.recipients != user);

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
                                ${encryptCondition ? email.body.slice(0, 99) : `
                                    <i class='fas fa-lock'></i> Encrypted message
                                `}
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
                                ${encryptCondition ? (`${email.body.slice(0, 99)} <a href='#'>(more...)</a>`) : `
                                    <i class='fas fa-lock'></i> Encrypted message
                                `}
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

            // Get cookie user email
            let user = getCookie('user_email')

            document.querySelector('#emails-view').innerHTML = '';

            const encryptCondition = email.encrypted && (email.sender != user);

            let emailCard = renderEmailView(email,
                `
                    <strong>Message:</strong> <br>
                    <div class='d-flex flex-column gap-4 ${encryptCondition ? 'text-center' : ''}'>
                        ${encryptCondition ? (
                    `
                                    <p>
                                        ${email.sender} has sent you a protected message. Please click the button below to view the message.
                                    </p>
                                    <i class='fas fa-lock'></i>
                                    <div>
                                        <button type='button' id='btn-read-secured-email' class='btn btn-primary'>
                                            Read the message
                                        </button>
                                    </div>
                                `
                ) : `<p>${email.body}</p>`
                }
                    </div>
                `
            )

            document.querySelector('#emails-view').appendChild(emailCard);
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

            // Handle for read secured email
            let readSecuredMsgBtn = document.querySelector('#btn-read-secured-email');
            readSecuredMsgBtn.addEventListener('click', () => handleReadSecuredMsg(email_id));

            document.querySelector('#emails-view').appendChild(replyBtn);
            read(email_id);
        })
}


/**
 * POST /emails
 */
function send_email() {
    event.preventDefault();

    let passphrase = ''
    const isSign = document.querySelector('#compose-sign').checked;
    if (isSign) {
        passphrase = document.querySelector('#compose-passphrase').value;
    }

    // POST /emails
    fetch('/emails', {
        method: 'POST',
        body: JSON.stringify({
            recipients: document.querySelector('#compose-recipients').value,
            subject: document.querySelector('#compose-subject').value,
            body: document.querySelector('#compose-body').value,
            encrypt: document.querySelector('#compose-encrypt').checked,
            sign: isSign,
            passphrase: passphrase
        })
    })
        .then(response => response.json())
        .then(result => {
            if (result.error) {
                // If #compose-to-error has child nodes, remove them
                if (document.querySelector('#compose-to-error').hasChildNodes()) {
                    document.querySelector('#compose-to-error').innerHTML = '';
                }

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


function capitalize_first_letter(string) {
    return string.replace(/\b\w/g, char => char.toUpperCase());
}


function getCookie(name) {
    const regex = new RegExp(`(^| )${name}=([^;]+)`)
    const match = document.cookie.match(regex)
    if (match) {
        const cleanedMatch = match[2].replace(/"/g, '')
        return cleanedMatch
    }
}


function handleReadSecuredMsg(email_id) {
    // Clear email view
    let emailView = document.querySelector('#emails-view');
    emailView.innerHTML = '';

    // Load passphrase input view
    emailView.appendChild(renderInputPassphrase());

    // Add event listener to submit passphrase
    let submitBtn = document.querySelector('#btn-submit-passphrase');
    submitBtn.addEventListener('click', () => {
        handleSubmitPassphrase(email_id);
    })
}


function handleSubmitPassphrase(email_id) {
    let passphraseValue = document.querySelector('#email-secured-passphrase').value;

    if (!passphraseValue) {
        document.querySelector('#error-email-passphrase').textContent = 'Passphrase is required';
    }

    fetch(`/emails/decrypt/${email_id}`, {
        method: 'POST',
        body: JSON.stringify({
            passphrase: passphraseValue
        })
    })
        .then(response => response.json())
        .then(result => {

            if (result.error) {
                console.error('Error decrypting message:', result.error);
                let errorDiv = document.querySelector('#error-email-passphrase');
                if (errorDiv.hasChildNodes()) {
                    errorDiv.innerHTML = '';
                }
                errorDiv.textContent = 'Invalid passphrase';
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
                    <span>This email is encrypted</span>
                </div>
            `);

            // Clear email view
            let emailView = document.querySelector('#emails-view');
            emailView.innerHTML = '';
            emailView.appendChild(emailCard);

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
        .catch(error => {
            console.error('Error fetching decrypted message:', error);
            let errorDiv = document.querySelector('#error-email-passphrase');
            if (errorDiv.hasChildNodes()) {
                errorDiv.innerHTML = '';
            }
            errorDiv.textContent = 'Invalid passphrase';
        });
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
                    <strong>From:</strong> <strong><span class='text-info'>${email.sender}</span></strong> &nbsp; |  &nbsp; <strong>To: </strong> <strong><span class='text-info'>${email.recipients}</span></strong> &nbsp; |  &nbsp; <strong>Date:</strong> ${email.timestamp} 
                    <br>
                </p>
                <div class='card-text' id='email-message'>
                    ${element}
                </div>

                ${flag ? flag : ''}
            </div>
        </div>
    `;

    return div;
}

function renderInputPassphrase() {
    let div = document.createElement('div');
    div.classList.add('h-half', 'd-flex', 'flex-column', 'justify-content-center');
    div.innerHTML = `
        <div class='mb-3'>
            <h3>Enter your passphrase to read the message</h3>
        </div>

        <div class='form-group row w-100 align-items-center'>
            <label for='email-secured-passphrase' class='col-sm-2 col-form-label d-flex align-items-center gap-2'>
                <i class='fas fa-key'></i>
                <span>Passphrase</span>
            </label>
            <div class='col-sm-8'>
                <input id='email-secured-passphrase' class='form-control'>
            </div>

            <div class='col-sm-2'>
                <button type='button' id='btn-submit-passphrase' class='btn btn-primary'>Submit</button>
            </div>
        </div>

        <div class='form-group row w-100'>
            <div class='col-sm-10 offset-sm-2'>
                <span id='error-email-passphrase' class='text-danger'></span>
            </div>
        </div>
    `;

    return div;
}