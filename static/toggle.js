const btn = document.getElementById('toggleBtn');

if (btn) {
    btn.addEventListener('click', async () => {
        btn.disabled = true;
        try {
            const res = await fetch('/toggle', {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                credentials: 'same-origin'
            });

            if (!res.ok) throw new Error(`HTTP ${res.status}`);

            const { state } = await res.json();
            btn.textContent = state ? 'ON' : 'OFF';
            btn.classList.toggle('on', state);
            btn.classList.toggle('off', !state);
        } catch (err) {
            console.error('Toggle failed:', err);
            alert('Could not toggle. Please try again.');
        } finally {
            btn.disabled = false;
        }
    });
}