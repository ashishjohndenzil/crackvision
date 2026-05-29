document.addEventListener("DOMContentLoaded", () => {
    updateLoginState();
});

function updateLoginState() {
    const navActions = document.getElementById('navActions');
    if (!navActions) return;

    const currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
    const currentAdmin = JSON.parse(localStorage.getItem('currentAdmin') || 'null');

    // 1. Admin is logged in
    if (currentAdmin && currentAdmin.role === 'admin') {
        navActions.innerHTML = `
            <a class="nav-button" href="admin.html">Admin Dashboard</a>
            <button type="button" class="nav-button button-link logout-button">Logout</button>
        `;
    } 
    // 2. Engineer is logged in
    else if (currentUser && currentUser.role === 'engineer') {
        navActions.innerHTML = `
            <a class="nav-button" href="engineer.html">Engineer Dashboard</a>
            <button type="button" class="nav-button button-link logout-button">Logout</button>
        `;
    } 
    // 3. Normal User is logged in
    else if (currentUser) {
        navActions.innerHTML = `
            <a class="nav-button" href="user.html">User Dashboard</a>
            <button type="button" class="nav-button button-link logout-button">Logout</button>
        `;
    } 
    // 4. Guest / Anonymous
    else {
        navActions.innerHTML = `
            <a class="nav-button nav-login" href="login.html">Login</a>
            <a class="nav-button nav-register" href="register.html">Register</a>
        `;
    }

    // Secondary UI buttons matching auth state (hero secondary login and contact action buttons)
    const heroLoginBtn = document.querySelector('.hero-secondary');
    if (heroLoginBtn) {
        if (currentUser || currentAdmin) {
            heroLoginBtn.style.display = 'none';
        } else {
            heroLoginBtn.style.display = 'inline-block';
        }
    }

    const contactActions = document.getElementById('contactActions');
    if (contactActions) {
        if (currentAdmin && currentAdmin.role === 'admin') {
            contactActions.innerHTML = '<a class="primary-button" href="admin.html">Admin Dashboard</a>';
        } else if (currentUser && currentUser.role === 'engineer') {
            contactActions.innerHTML = '<a class="primary-button" href="engineer.html">Engineer Dashboard</a>';
        } else if (currentUser) {
            contactActions.innerHTML = `<span class="nav-user">Logged in as ${currentUser.name}</span>`;
        } else {
            contactActions.innerHTML = `
                <a class="primary-button" href="register.html">Register</a>
                <a class="secondary-button" href="login.html">Login</a>
            `;
        }
    }

    // Attach click listener to logout buttons
    document.querySelectorAll('.logout-button').forEach(button => {
        button.addEventListener('click', () => {
            localStorage.removeItem('currentUser');
            localStorage.removeItem('currentAdmin');
            window.location.href = 'login.html';
        });
    });
}
