document.addEventListener('DOMContentLoaded', () => {
    const signupBtn = document.getElementById('signupBtn');
    if (signupBtn) {
        signupBtn.onclick = async () => {
            const username = document.getElementById('username').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            const response = await fetch('/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password }),
            });

            if (response.ok) {
                window.location.href = '/';
            } else {
                const error = await response.json();
                alert(error.detail);
            }
        };
    }

    const signinBtn = document.getElementById('signinBtn');
    if (signinBtn) {
        signinBtn.onclick = async () => {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);

            const response = await fetch('/signin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: formData,
            });

            if (response.ok) {
                window.location.href = '/';
            } else {
                try {
                    const error = await response.json();
                    alert(error.detail);
                } catch {
                    alert("An unknown error occurred during sign-in.");
                }
            }
        };
    }
});
