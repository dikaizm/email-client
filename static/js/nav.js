document.addEventListener('DOMContentLoaded', function () {
    const currentPath = window.location.pathname;

    const inboxNav = document.getElementById('inbox');
    const sentNav = document.getElementById('sent');
    const securityNav = document.getElementById('security');

    if (currentPath === '/') {
        inboxNav.classList.add('active');
    } else if (currentPath === '/sent') {
        sentNav.classList.add('active');
    } else if (currentPath === '/security') {
        securityNav.classList.add('active');
    }
})