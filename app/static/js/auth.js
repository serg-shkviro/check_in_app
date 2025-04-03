document.addEventListener('DOMContentLoaded', () => {
    sessionStorage.removeItem('user');

    // Elements
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    
    // Show toast notification
    function showToast(title, description, type = 'success') {
      const toastContainer = document.getElementById('toast-container');
      
      const toast = document.createElement('div');
      toast.className = `toast toast-${type}`;
      toast.innerHTML = `
        <div class="toast-icon">
          <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        </div>
        <div class="toast-content">
          <div class="toast-title">${title}</div>
          <div class="toast-description">${description}</div>
        </div>
      `;
      
      toastContainer.appendChild(toast);
      
      // Remove toast after 3 seconds
      setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
          toast.remove();
        }, 300);
      }, 3000);
    }
    
    // Handle login form submission
    if (loginForm) {
      loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const email = loginForm.email.value;
        const password = loginForm.password.value;
        
        fetch('/sing_in', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        })
        .then(response => response.json())
        .then(data => {
          if (data.message) {
            showToast('Успешный вход', data.message, 'success');
            const name = data.name;
            sessionStorage.setItem('user', JSON.stringify({ name, email, password }));
            setTimeout(() => {
              window.location.href = '/map';
            }, 1000);
          } else {
            showToast('Ошибка входа', data.error, 'error');
          }
        });
      });
    }
    
    // Handle registration form submission
    if (registerForm) {
      registerForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const name = registerForm.name.value;
        const email = registerForm.email.value;
        const password = registerForm.password.value;
        const confirmPassword = registerForm['confirm-password'].value;
        
        // Simple validation
        if (!name || !email || !password || !confirmPassword) {
          showToast('Ошибка регистрации', 'Пожалуйста, заполните все поля', 'error');
          return;
        }
        
        // Password match validation
        if (password !== confirmPassword) {
          showToast('Ошибка регистрации', 'Пароли не совпадают', 'error');
          return;
        }
        
        // Password length validation
        if (password.length < 8) {
          showToast('Ошибка регистрации', 'Пароль должен содержать не менее 8 символов', 'error');
          return;
        }
        
        fetch('/sing_up', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, email, password, confirmPassword })
        })
        .then(response => response.json())
        .then(data => {
          if (data.message) {
            showToast('Успешная регистрация', data.message, 'success');
            sessionStorage.setItem('user', JSON.stringify({ name, email, password }));
            setTimeout(() => {
              window.location.href = '/map';
            }, 1000);
          } else {
            showToast('Ошибка регистрации', data.error, 'error');
          }
        });
      });
    }
  });