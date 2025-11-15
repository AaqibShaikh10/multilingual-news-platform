// Main JavaScript functionality for Multilingual News Analysis Platform

document.addEventListener('DOMContentLoaded', function() {
    // Initialize input method switching
    initializeInputMethods();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize Bootstrap components
    initializeBootstrapComponents();
    
    // Initialize copy-to-clipboard functionality
    initializeCopyToClipboard();
    
    // Initialize RSS functionality
    initializeRSSFunctionality();
});

function initializeInputMethods() {
    const inputMethods = document.querySelectorAll('input[name="input_method"]');
    const textSection = document.getElementById('text_input_section');
    const urlSection = document.getElementById('url_input_section');
    const fileSection = document.getElementById('file_input_section');
    const rssSection = document.getElementById('rss_input_section');
    
    inputMethods.forEach(method => {
        method.addEventListener('change', function() {
            // Hide all sections
            if (textSection) textSection.style.display = 'none';
            if (urlSection) urlSection.style.display = 'none';
            if (fileSection) fileSection.style.display = 'none';
            if (rssSection) rssSection.style.display = 'none';
            
            // Show selected section
            switch(this.value) {
                case 'text':
                    if (textSection) {
                        textSection.style.display = 'block';
                        const textArea = document.getElementById('direct_text');
                        if (textArea) textArea.focus();
                    }
                    break;
                case 'url':
                    if (urlSection) {
                        urlSection.style.display = 'block';
                        const urlInput = document.getElementById('url');
                        if (urlInput) urlInput.focus();
                    }
                    break;
                case 'file':
                    if (fileSection) fileSection.style.display = 'block';
                    break;
                case 'rss':
                    if (rssSection) rssSection.style.display = 'block';
                    break;
            }
        });
    });
}

function initializeFormValidation() {
    const form = document.getElementById('analysisForm');
    if (!form) return;
    
    const submitBtn = document.getElementById('analyzeBtn');
    const submitText = document.getElementById('analyzeText');
    const submitSpinner = document.getElementById('analyzeSpinner');
    
    form.addEventListener('submit', function(e) {
        // Clear previous validation
        clearValidationErrors();
        
        // Get current input method
        const inputMethod = document.querySelector('input[name="input_method"]:checked');
        if (!inputMethod) {
            e.preventDefault();
            showError('Please select an input method.');
            return;
        }
        
        // Validate based on input method
        let isValid = false;
        let errorMessage = '';
        
        switch(inputMethod.value) {
            case 'text':
                const textInput = document.getElementById('direct_text');
                const text = textInput ? textInput.value.trim() : '';
                if (text.length < 50) {
                    errorMessage = 'Please enter at least 50 characters of text for meaningful analysis.';
                } else if (text.length > 50000) {
                    errorMessage = 'Text is too long. Maximum 50,000 characters allowed.';
                } else {
                    isValid = true;
                }
                break;
                
            case 'url':
                const urlInput = document.getElementById('url');
                const url = urlInput ? urlInput.value.trim() : '';
                if (!url) {
                    errorMessage = 'Please enter a URL.';
                } else if (!isValidUrl(url)) {
                    errorMessage = 'Please enter a valid URL starting with http:// or https://';
                } else {
                    isValid = true;
                }
                break;
                
            case 'file':
                const fileInput = document.getElementById('file');
                if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
                    errorMessage = 'Please select a file to upload.';
                } else {
                    const file = fileInput.files[0];
                    const maxSize = 16 * 1024 * 1024; // 16MB
                    if (file.size > maxSize) {
                        errorMessage = 'File size too large. Maximum 16MB allowed.';
                    } else if (!isValidFileType(file.name)) {
                        errorMessage = 'Invalid file type. Only .txt and .pdf files are allowed.';
                    } else {
                        isValid = true;
                    }
                }
                break;
                
            case 'rss':
                const rssUrl = document.getElementById('rss_url');
                const rssUrlValue = rssUrl ? rssUrl.value.trim() : '';
                const selectedArticle = document.querySelector('input[name="article_index"]:checked');
                
                if (!rssUrlValue) {
                    errorMessage = 'Please enter an RSS feed URL.';
                } else if (!isValidUrl(rssUrlValue)) {
                    errorMessage = 'Please enter a valid RSS feed URL.';
                } else if (document.querySelector('input[name="article_index"]') && !selectedArticle) {
                    errorMessage = 'Please select an article to analyze.';
                } else {
                    isValid = true;
                }
                break;
        }
        
        if (!isValid) {
            e.preventDefault();
            showError(errorMessage);
            return;
        }
        
        // Show loading state
        if (submitBtn && submitText && submitSpinner) {
            submitText.style.display = 'none';
            submitSpinner.style.display = 'inline';
            submitBtn.disabled = true;
            
            // Add timeout to reset if something goes wrong
            setTimeout(() => {
                if (submitBtn.disabled) {
                    resetSubmitButton();
                }
            }, 60000); // 60 seconds timeout
        }
    });
}

function initializeBootstrapComponents() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

function initializeCopyToClipboard() {
    // Add copy functionality to results
    const copyButtons = document.querySelectorAll('.copy-btn');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                copyToClipboard(targetElement.textContent);
                showSuccess('Copied to clipboard!');
            }
        });
    });
}

function initializeRSSFunctionality() {
    // Set popular RSS URL functionality
    window.setRssUrl = function(url) {
        const rssInput = document.getElementById('rss_url');
        if (rssInput) {
            rssInput.value = url;
        }
    };
}

// Utility functions
function isValidUrl(string) {
    try {
        const url = new URL(string);
        return url.protocol === 'http:' || url.protocol === 'https:';
    } catch (_) {
        return false;
    }
}

function isValidFileType(filename) {
    const validExtensions = ['.txt', '.pdf'];
    return validExtensions.some(ext => filename.toLowerCase().endsWith(ext));
}

function showError(message) {
    const alertHtml = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="fas fa-exclamation-triangle me-2"></i>${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    showAlert(alertHtml);
}

function showSuccess(message) {
    const alertHtml = `
        <div class="alert alert-success alert-dismissible fade show" role="alert">
            <i class="fas fa-check-circle me-2"></i>${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    showAlert(alertHtml);
}

function showAlert(alertHtml) {
    const container = document.querySelector('main .container');
    if (container) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = alertHtml;
        container.insertBefore(tempDiv.firstElementChild, container.firstElementChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = container.querySelector('.alert');
            if (alert && typeof bootstrap !== 'undefined') {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }
}

function clearValidationErrors() {
    const alerts = document.querySelectorAll('.alert-danger');
    alerts.forEach(alert => {
        if (typeof bootstrap !== 'undefined') {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        } else {
            alert.remove();
        }
    });
}

function resetSubmitButton() {
    const submitBtn = document.getElementById('analyzeBtn');
    const submitText = document.getElementById('analyzeText');
    const submitSpinner = document.getElementById('analyzeSpinner');
    
    if (submitBtn && submitText && submitSpinner) {
        submitText.style.display = 'inline';
        submitSpinner.style.display = 'none';
        submitBtn.disabled = false;
    }
}

function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            document.execCommand('copy');
        } catch (err) {
            console.error('Unable to copy to clipboard', err);
        }
        document.body.removeChild(textArea);
    }
}

// Character counter for text input
function updateCharacterCount() {
    const textArea = document.getElementById('direct_text');
    const counter = document.getElementById('char_counter');
    
    if (textArea && counter) {
        const length = textArea.value.length;
        counter.textContent = `${length} characters`;
        
        if (length < 50) {
            counter.className = 'form-text text-danger';
        } else if (length > 45000) {
            counter.className = 'form-text text-warning';
        } else {
            counter.className = 'form-text text-muted';
        }
    }
}

// File size validation
function validateFileSize(input) {
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const maxSize = 16 * 1024 * 1024; // 16MB
        
        if (file.size > maxSize) {
            showError('File size too large. Maximum 16MB allowed.');
            input.value = '';
            return false;
        }
    }
    return true;
}

// Add event listeners for dynamic validation
document.addEventListener('DOMContentLoaded', function() {
    const textArea = document.getElementById('direct_text');
    if (textArea) {
        textArea.addEventListener('input', updateCharacterCount);
    }
    
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            validateFileSize(this);
        });
    }
});
