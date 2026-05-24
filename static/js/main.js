/**
 * Sports Day 2026 — Main JavaScript
 * University of the Punjab, Lahore
 */

document.addEventListener('DOMContentLoaded', function () {

    // ── Auto-dismiss alerts after 5 seconds ──
    const alerts = document.querySelectorAll('.alert.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // ── Confirm delete / cancel actions ──
    document.querySelectorAll('[data-confirm]').forEach(function (el) {
        el.addEventListener('click', function (e) {
            if (!confirm(el.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // ── Password strength indicator ──
    const pwField = document.getElementById('password');
    if (pwField) {
        pwField.addEventListener('input', function () {
            const val = pwField.value;
            let strength = 0;
            if (val.length >= 6)  strength++;
            if (val.length >= 10) strength++;
            if (/[A-Z]/.test(val)) strength++;
            if (/[0-9]/.test(val)) strength++;
            if (/[^A-Za-z0-9]/.test(val)) strength++;

            let bar = document.getElementById('pw-strength');
            if (!bar) {
                bar = document.createElement('div');
                bar.id = 'pw-strength';
                bar.className = 'progress mt-1';
                bar.style.height = '4px';
                bar.innerHTML = '<div class="progress-bar" role="progressbar"></div>';
                pwField.parentElement.after(bar);
            }
            const fill = bar.querySelector('.progress-bar');
            const pct  = (strength / 5) * 100;
            fill.style.width = pct + '%';
            fill.className = 'progress-bar bg-' + (
                pct < 40 ? 'danger' : pct < 70 ? 'warning' : 'success'
            );
        });
    }

    // ── Confirm password match ──
    const confirmPw = document.getElementById('confirm_password');
    if (confirmPw && pwField) {
        confirmPw.addEventListener('input', function () {
            if (confirmPw.value && confirmPw.value !== pwField.value) {
                confirmPw.setCustomValidity('Passwords do not match');
                confirmPw.classList.add('is-invalid');
            } else {
                confirmPw.setCustomValidity('');
                confirmPw.classList.remove('is-invalid');
            }
        });
    }

    // ── Tooltip initialisation ──
    const tooltipEls = document.querySelectorAll('[title]');
    tooltipEls.forEach(function (el) {
        new bootstrap.Tooltip(el, { trigger: 'hover' });
    });

    // ── Back-to-top button ──
    const topBtn = document.createElement('button');
    topBtn.id = 'back-to-top';
    topBtn.innerHTML = '<i class="bi bi-arrow-up"></i>';
    topBtn.style.cssText = [
        'position:fixed', 'bottom:24px', 'right:24px', 'z-index:999',
        'border:none', 'border-radius:50%', 'width:40px', 'height:40px',
        'background:#1a56db', 'color:#fff', 'cursor:pointer',
        'display:none', 'box-shadow:0 4px 12px rgba(0,0,0,0.2)',
        'transition:all 0.2s'
    ].join(';');
    document.body.appendChild(topBtn);

    window.addEventListener('scroll', function () {
        topBtn.style.display = window.scrollY > 300 ? 'block' : 'none';
    });
    topBtn.addEventListener('click', function () {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

});
