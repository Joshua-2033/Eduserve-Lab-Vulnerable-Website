document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('menuToggle');
  const sidebar = document.getElementById('sidebar');
  if (toggle && sidebar) toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  document.querySelectorAll('[data-toggle-password]').forEach(button => {
    button.addEventListener('click', () => {
      const input = document.getElementById(button.dataset.togglePassword);
      if (!input) return;
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      button.textContent = show ? 'Hide' : 'Show';
      button.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
    });
  });
  document.querySelectorAll('form').forEach(form => form.addEventListener('submit', () => {
    const button = form.querySelector('button[type="submit"],button:not([type])');
    if (button && !button.dataset.noLoading) { button.dataset.originalText = button.textContent; }
  }));
});
