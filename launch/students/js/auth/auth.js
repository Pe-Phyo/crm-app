import { apiCall, login } from '../api.js';

const setupScreen = document.getElementById('setupScreen');
const loginScreen = document.getElementById('loginScreen');
const mainPanel = document.getElementById('mainPanel');
const setupPassword = document.getElementById('setupPassword');
const setupConfirm = document.getElementById('setupConfirm');
const setupBtn = document.getElementById('setupBtn');
const setupError = document.getElementById('setupError');
const passwordInput = document.getElementById('passwordInput');
const loginBtn = document.getElementById('loginBtn');
const loginError = document.getElementById('loginError');

export function showSetup() {
    setupScreen.style.display = 'block';
    loginScreen.style.display = 'none';
    mainPanel.style.display = 'none';
}

export function showLogin() {
    setupScreen.style.display = 'none';
    loginScreen.style.display = 'block';
    mainPanel.style.display = 'none';
}

export function showMain() {
    setupScreen.style.display = 'none';
    loginScreen.style.display = 'none';
    mainPanel.style.display = 'block';
}

export async function checkSetup() {
    try {
        const status = await apiCall('GET', '/auth/status', null, true);
        if (status.setup) {
            showLogin();
        } else {
            showSetup();
        }
    } catch (e) {
        showLogin();   // fallback: assume setup is complete
    }
}

export function bindAuthEvents(onLoginSuccess) {
    setupBtn.addEventListener('click', async () => {
        const pw = setupPassword.value;
        const confirm = setupConfirm.value;
        if (pw.length < 6) {
            setupError.textContent = 'Min 6 characters';
            return;
        }
        if (pw !== confirm) {
            setupError.textContent = 'Passwords do not match';
            return;
        }
        try {
            await apiCall('POST', '/auth/setup', { password: pw }, true);
            await login(pw);
            showMain();
            if (onLoginSuccess) onLoginSuccess();
        } catch (e) {
            setupError.textContent = e.message;
        }
    });

    loginBtn.addEventListener('click', async () => {
        try {
            await login(passwordInput.value);
            showMain();
            if (onLoginSuccess) onLoginSuccess();
        } catch (e) {
            loginError.textContent = 'Wrong password';
        }
    });

    passwordInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') loginBtn.click();
    });
}