document.addEventListener('DOMContentLoaded', function () {
    load_security();
});

/**
 * GET /security
 */
function load_security() {
    // Show the security view (PGP key pair and other user saved public key) and hide other views
    document.querySelector('#security-view').style.display = 'block';

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

            if (result.length === 0) {
                const noKey = document.createElement('div')
                noKey.classList.add('text-center', 'mt-3')
                noKey.innerHTML = `
                    <div class='alert alert-dark' role='alert'>
                        No key pair generated
                    </div>
                `;

                myPgpKey.appendChild(noKey);
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
                        ${userKeysTable(result)}
                    </tbody>
                </table>
            `;

            myPgpKey.appendChild(myPgpKeyTable);
            handle_user_key_item();
        });

    pageView.appendChild(myPgpKey);

    // Received public key
    const receivedPublicKey = document.createElement('div')
    receivedPublicKey.style.marginTop = '2rem';

    const receivedPublicKeyHeader = document.createElement('div')
    receivedPublicKey.innerHTML = `
        <div>
            <h5>User Keys</h5>
            <span class='badge bg-info'>Public keys received from other users</span>
        </div>
        <!--
        <div>
            <button type='button' class='btn btn-primary' id='btn-import-received-key'>
                <i class='fas fa-plus'></i> Import a public key
            </button>
        </div>
        -->
    `

    receivedPublicKey.appendChild(receivedPublicKeyHeader)

    // GET /security/received_keys
    fetch('/api/security/received-keys', {
        method: 'GET'
    })
        .then(response => response.json())
        .then(result => {

            if (result.error) {
                const errorMsg = document.createElement('span')
                errorMsg.textContent = result.error
                receivedPublicKey.appendChild(errorMsg)
                return
            }

            if (result.length === 0) {
                const noKey = document.createElement('div')
                noKey.classList.add('text-center', 'mt-3')
                noKey.innerHTML = `
                    <div class='alert alert-dark' role='alert'>
                        No user public key received
                    </div>
                `;

                receivedPublicKey.appendChild(noKey);
                return
            }

            const receivedPublicKeyTable = document.createElement('div')
            receivedPublicKeyTable.innerHTML = `
                <table class='table table-hover table-dark mt-3'>
                    <thead>
                        <tr>
                            <th scope="col">#</th>
                            <th scope="col">User</th>
                            <th scope="col">Email</th>
                            <th scope="col">Key ID</th>
                            <th scope="col">Expire</th>
                            <th scope="col">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${receivedPublicKeysTable(result)}
                    </tbody>
                </table>
            `;

            receivedPublicKey.appendChild(receivedPublicKeyTable);
            handle_received_key_item();
        })

    // pageView.appendChild(receivedPublicKey);

    // Button to show generate key pair form
    document.querySelector('#btn-generate-key-form').addEventListener('click', form_generate_key);
}


function handle_user_key_item() {
    document.querySelectorAll('.btn-user-key-detail').forEach(button => {
        button.addEventListener('click', function () {
            const keyId = this.getAttribute('data-key-id');
            fetch(`/api/security/keys/${keyId}`, { method: 'GET' })
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


function handle_received_key_item() {
    document.querySelectorAll('.btn-received-key-detail').forEach(button => {
        button.addEventListener('click', function () {
            const keyId = this.getAttribute('data-key-id');
            fetch(`/api/security/received-keys/${keyId}`, { method: 'GET' })
                .then(response => response.json())
                .then(data => {
                    received_key_detail(data);
                })
                .catch(error => {
                    console.error('Error fetching key details:', error);
                });
        });
    });

    document.querySelectorAll('.btn-received-key-delete').forEach(button => {
        button.addEventListener('click', function () {
            const keyId = this.getAttribute('data-key-id');
            fetch(`/api/security/received-keys/${keyId}`, { method: 'DELETE' })
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


function userKeysTable(data) {
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


function receivedPublicKeysTable(data) {
    const tableRows = data.map((item, index) => {
        const fullname = `${item.owner_first_name} ${item.owner_last_name}`;

        return `
        <tr>
            <th scope="row">${index + 1}</th>
            <td>${fullname}</td>
            <td>${item.owner_email}</td>
            <td class='w-30 text-break'>${item.key_id}</td>
            <td>${item.expire_date}</td>
            <td>
                <button type='button' class='btn btn-primary btn-received-key-detail' data-key-id='${item.key_id}' title='detail'>
                    <i class='fas fa-eye'></i>
                </button>
                <button type='button' class='btn btn-danger btn-received-key-delete' data-key-id='${item.key_id}' title='delete'>
                    <i class='fas fa-trash'></i>
                </button>
            </td>
        </tr>
        `
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
        let objToArr = Object.entries(data).map(([key, value]) => {
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
        <div class="d-flex justify-content-between align-items-center">
            <h3 class='mb-4'>Key Details</h3>
            ${!data.default_key ? `<button type="button" id="btn-set-default-key" class='btn btn-primary' style="height: fit-content">
                Set as default
            </button>` : ''}
        </div>
        
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

    const setDefaultKeyBtn = document.getElementById('btn-set-default-key');
    setDefaultKeyBtn.addEventListener('click', () => {
        console.log('click btn default key')

        fetch(`/api/security/keys/${data.key_id}`, {
            method: 'PUT',
            body: JSON.stringify({
                default_key: true
            }),
        }).then(res => {
            if (!res.ok) return alert('Failed to set default key');
            return res.json();
        }).then(data => {
            console.log(data);
            load_security();
        })
    })
}

/**
 * 
 * @param data {owner_first_name, owner_last_name, owner_email, key_id, public_key, expire_date}
 */
function received_key_detail(data) {
    const securityView = document.querySelector('#security-view');
    securityView.innerHTML = '';

    function key_mapper(key) {
        const keyMap = {
            'owner': 'User',
            'owner_email': 'Email',
            'key_id': 'Key ID',
            'public_key': 'Public Key',
            'expire_date': 'Expire Date',
        };

        return keyMap[key] || key;
    }

    function key_detail_rows() {
        data['owner'] = `${data['owner_first_name']} ${data['owner_last_name']}`;
        delete data['owner_first_name'];
        delete data['owner_last_name'];

        // Create a new object with 'owner' as the first key
        let newData = { owner: data.owner };
        for (let key in data) {
            if (key !== 'owner') {
                newData[key] = data[key];
            }
        }

        // Convert the object to an array of key-value pairs
        let objToArr = Object.entries(newData).map(([key, value]) => {
            return { key: key, value: value };
        });

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


function capitalize_first_letter(string) {
    return string.replace(/\b\w/g, char => char.toUpperCase());
}