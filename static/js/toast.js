/**
 * Toast Notification System
 * Simple, VaWW-compatible toast notifications using daisyUI alert classes
 */

/**
 * Show a toast notification
 * @param {string} message - The message to display
 * @param {string} type - Type of toast: 'success', 'error', 'warning', 'info'
 * @param {number} duration - Duration in milliseconds (default: 3000ms for success/info, 5000ms for error/warning)
 */
window.showToast = function(message, type = 'info', duration = null) {
    // Default durations based on type
    if (duration === null) {
        duration = (type === 'error' || type === 'warning') ? 5000 : 3000;
    }

    // Get toast container with fallback to alert
    const container = document.getElementById('toast-container');
    if (!container) {
        console.error('Toast container not found');
        alert(message);  // Graceful degradation
        return;
    }

    // HTML escape function to prevent XSS
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Sanitize message
    const safeMessage = escapeHtml(String(message));

    // Create toast element
    const toast = document.createElement('div');
    toast.className = 'toast-item mb-2 w-80';

    // Map type to daisyUI alert classes and icons
    const typeConfig = {
        success: {
            alertClass: 'alert-success',
            icon: '✓',
            bgColor: 'bg-success',
            textColor: 'text-success-content'
        },
        error: {
            alertClass: 'alert-error',
            icon: '✕',
            bgColor: 'bg-error',
            textColor: 'text-error-content'
        },
        warning: {
            alertClass: 'alert-warning',
            icon: '⚠',
            bgColor: 'bg-warning',
            textColor: 'text-warning-content'
        },
        info: {
            alertClass: 'alert-info',
            icon: 'ℹ',
            bgColor: 'bg-info',
            textColor: 'text-info-content'
        }
    };

    const config = typeConfig[type] || typeConfig.info;

    // Build toast HTML with sanitized message and ARIA support
    toast.innerHTML = `
        <div class="alert ${config.alertClass} shadow-lg animate-slide-in-right flex items-center justify-between" role="alert">
            <div class="flex items-center gap-2">
                <span class="text-lg font-bold" aria-hidden="true">${config.icon}</span>
                <span>${safeMessage}</span>
            </div>
            <button class="btn btn-ghost btn-sm btn-circle"
                    aria-label="Benachrichtigung schließen"
                    onclick="this.closest('.toast-item').remove()">
                ✕
            </button>
        </div>
    `;

    // Add to container
    container.appendChild(toast);

    // Auto-dismiss after duration
    if (duration > 0) {
        setTimeout(() => {
            // Add fade-out animation
            const alert = toast.querySelector('.alert');
            if (alert) {
                alert.classList.remove('animate-slide-in-right');
                alert.classList.add('animate-slide-out-right');

                // Remove from DOM after animation
                setTimeout(() => {
                    toast.remove();
                }, 300);
            }
        }, duration);
    }
};

// Add CSS animations inline (will be compiled by Tailwind)
if (!document.getElementById('toast-styles')) {
    const style = document.createElement('style');
    style.id = 'toast-styles';
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }

        .animate-slide-in-right {
            animation: slideInRight 0.3s ease-out;
        }

        .animate-slide-out-right {
            animation: slideOutRight 0.3s ease-in;
        }
    `;
    document.head.appendChild(style);
}

/**
 * Set button loading state
 * @param {HTMLElement} button - The button element
 * @param {boolean} isLoading - Whether the button is loading
 */
window.setButtonLoading = function(button, isLoading) {
    if (!button) {
        console.error('setButtonLoading: Button element is null');
        return;
    }

    if (isLoading) {
        // Store original content and disabled state
        button.dataset.originalContent = button.innerHTML;
        button.dataset.wasDisabled = button.disabled ? 'true' : 'false';

        // Disable button
        button.disabled = true;

        // Add loading spinner before existing content
        const spinner = '<span class="loading loading-spinner loading-sm mr-2"></span>';
        button.innerHTML = spinner + button.textContent.trim();
    } else {
        // Restore original content
        if (button.dataset.originalContent) {
            button.innerHTML = button.dataset.originalContent;
        }

        // Restore original disabled state
        button.disabled = button.dataset.wasDisabled === 'true';

        // Clean up data attributes
        delete button.dataset.originalContent;
        delete button.dataset.wasDisabled;
    }
};
