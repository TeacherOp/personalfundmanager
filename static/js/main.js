// Personal Fund Manager - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initToggleValues();
    initSyncButton();
    initBucketActions();
    initAssignButtons();
    initBucketFilter();
    initModalClose();
});

// Toggle value visibility
function initToggleValues() {
    const toggleBtn = document.getElementById('toggleValues');
    if (!toggleBtn) return;

    toggleBtn.addEventListener('click', async function() {
        try {
            const response = await fetch('/api/toggle-values', { method: 'POST' });
            const data = await response.json();

            if (data.success) {
                document.body.classList.toggle('values-hidden', data.hidden);
            }
        } catch (error) {
            showToast('Failed to toggle values', 'error');
        }
    });
}

// Sync from Groww
function initSyncButton() {
    const syncBtn = document.getElementById('syncBtn');
    if (!syncBtn) return;

    syncBtn.addEventListener('click', async function() {
        syncBtn.disabled = true;
        syncBtn.textContent = 'Syncing...';

        try {
            const response = await fetch('/api/sync', { method: 'POST' });
            const data = await response.json();

            if (data.success) {
                showToast('Sync completed successfully', 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                showToast(data.error || 'Sync failed', 'error');
            }
        } catch (error) {
            showToast('Sync failed: ' + error.message, 'error');
        } finally {
            syncBtn.disabled = false;
            syncBtn.textContent = 'Sync from Groww';
        }
    });
}

// Bucket actions (add, edit, delete)
function initBucketActions() {
    const addBucketBtn = document.getElementById('addBucketBtn');
    if (addBucketBtn) {
        addBucketBtn.addEventListener('click', () => showBucketModal());
    }

    // Edit bucket buttons
    document.querySelectorAll('.edit-bucket').forEach(btn => {
        btn.addEventListener('click', function() {
            const card = this.closest('.bucket-card');
            const bucketId = card.dataset.bucketId;
            const name = card.querySelector('h4').textContent;
            const philosophy = card.querySelector('.bucket-philosophy')?.textContent || '';
            const target = card.querySelector('.stat:nth-child(4) .value')?.textContent.replace('%', '') || '0';

            showBucketModal({
                id: bucketId,
                name: name,
                philosophy: philosophy,
                growth_target: parseInt(target)
            });
        });
    });

    // Delete bucket buttons
    document.querySelectorAll('.delete-bucket').forEach(btn => {
        btn.addEventListener('click', async function() {
            const card = this.closest('.bucket-card');
            const bucketId = card.dataset.bucketId;
            const name = card.querySelector('h4').textContent;

            if (!confirm(`Delete bucket "${name}"? Holdings will be unassigned.`)) return;

            try {
                const response = await fetch(`/api/bucket/${bucketId}`, { method: 'DELETE' });
                const data = await response.json();

                if (data.success) {
                    showToast('Bucket deleted', 'success');
                    card.remove();
                    setTimeout(() => location.reload(), 1000);
                }
            } catch (error) {
                showToast('Failed to delete bucket', 'error');
            }
        });
    });
}

// Show bucket modal
function showBucketModal(bucket = null) {
    const template = document.getElementById('bucket-form-template');
    const content = template.content.cloneNode(true);

    if (bucket) {
        content.querySelector('[name="bucket_id"]').value = bucket.id;
        content.querySelector('[name="name"]').value = bucket.name;
        content.querySelector('[name="philosophy"]').value = bucket.philosophy || '';
        content.querySelector('[name="description"]').value = bucket.description || '';
        content.querySelector('[name="growth_target"]').value = bucket.growth_target || 15;
    }

    showModal(bucket ? 'Edit Bucket' : 'Create Bucket', content);

    document.getElementById('bucketForm').addEventListener('submit', async function(e) {
        e.preventDefault();

        const formData = new FormData(this);
        const bucketId = formData.get('bucket_id');
        const payload = {
            name: formData.get('name'),
            philosophy: formData.get('philosophy'),
            description: formData.get('description'),
            growth_target: parseInt(formData.get('growth_target')) || 0
        };

        try {
            const url = bucketId ? `/api/bucket/${bucketId}` : '/api/bucket';
            const method = bucketId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (data.success) {
                showToast(bucketId ? 'Bucket updated' : 'Bucket created', 'success');
                hideModal();
                setTimeout(() => location.reload(), 1000);
            }
        } catch (error) {
            showToast('Failed to save bucket', 'error');
        }
    });
}

// Assign holding to bucket
function initAssignButtons() {
    document.querySelectorAll('.assign-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const isin = this.dataset.isin;
            const row = this.closest('tr');
            const symbol = row.querySelector('.symbol').textContent;

            showAssignModal(isin, symbol);
        });
    });
}

function showAssignModal(isin, symbol) {
    const template = document.getElementById('assign-form-template');
    const content = template.content.cloneNode(true);
    content.querySelector('[name="isin"]').value = isin;

    showModal(`Assign ${symbol}`, content);

    document.getElementById('assignForm').addEventListener('submit', async function(e) {
        e.preventDefault();

        const formData = new FormData(this);
        const payload = {
            bucket_id: formData.get('bucket_id'),
            purchased_by: formData.get('purchased_by')
        };

        try {
            const response = await fetch(`/api/holding/${isin}/assign`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (data.success) {
                showToast('Holding assigned', 'success');
                hideModal();
                setTimeout(() => location.reload(), 1000);
            }
        } catch (error) {
            showToast('Failed to assign holding', 'error');
        }
    });
}

// Bucket filter
function initBucketFilter() {
    const filter = document.getElementById('bucketFilter');
    if (!filter) return;

    filter.addEventListener('change', function() {
        const value = this.value;
        const rows = document.querySelectorAll('.holdings-table tbody tr');

        rows.forEach(row => {
            const bucket = row.dataset.bucket;
            if (value === 'all' || bucket === value) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
}

// Modal helpers
function showModal(title, content) {
    const overlay = document.getElementById('modal-overlay');
    const modalTitle = document.getElementById('modal-title');
    const modalContent = document.getElementById('modal-content');

    modalTitle.textContent = title;
    modalContent.innerHTML = '';
    modalContent.appendChild(content);
    overlay.classList.remove('hidden');
}

function hideModal() {
    const overlay = document.getElementById('modal-overlay');
    overlay.classList.add('hidden');
}

function initModalClose() {
    const overlay = document.getElementById('modal-overlay');

    overlay.addEventListener('click', function(e) {
        if (e.target === overlay || e.target.classList.contains('modal-close')) {
            hideModal();
        }
    });

    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal-close-btn')) {
            hideModal();
        }
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            hideModal();
        }
    });
}

// Toast notifications
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = 'toast ' + type;

    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}
