// Vanilla JavaScript for ProjectHub (Interactions & Validations)

document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto-scroll chat box to bottom on page load
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // 2. Validate ZIP file upload extension on project creation
    const uploadForm = document.getElementById('create-project-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', (e) => {
            const fileInput = document.getElementById('project_file');
            if (fileInput && fileInput.files.length > 0) {
                const fileName = fileInput.files[0].name.toLowerCase();
                if (!fileName.endsWith('.zip')) {
                    e.preventDefault();
                    alert('Please select a valid .zip file for project upload.');
                }
            }
        });
    }

    // 3. Confirm status change for project owner
    const statusSelect = document.getElementById('status-select');
    if (statusSelect) {
        const initialStatus = statusSelect.value;
        statusSelect.form.addEventListener('submit', (e) => {
            if (statusSelect.value === initialStatus) {
                e.preventDefault();
                alert('Please select a different status before updating.');
            }
        });
    }

    // 4. Thesis generation loading state indicator
    const thesisBtn = document.getElementById('generate-thesis-btn');
    if (thesisBtn) {
        thesisBtn.addEventListener('click', () => {
            thesisBtn.innerText = 'Generating Thesis...';
            thesisBtn.style.opacity = '0.7';
            thesisBtn.style.pointerEvents = 'none';
        });
    }

    // 5. Auto-dismiss flash alert messages after 4 seconds
    const alerts = document.querySelectorAll('.alert');
    if (alerts.length > 0) {
        setTimeout(() => {
            alerts.forEach((alert) => {
                alert.style.transition = 'opacity 0.4s ease';
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 400);
            });
        }, 4000);
    }
});
