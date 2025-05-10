// Stripe Checkout Integration with Analytics and Error Handling
const stripe = Stripe('pk_test_xxx_your_public_key_here');

// Analytics tracking
const analytics = {
    trackEvent: function(eventName, properties = {}) {
        // Send to analytics service
        console.log(`[Analytics] ${eventName}:`, properties);
    },
    
    trackError: function(error, context = {}) {
        console.error(`[Error] ${error.message}:`, context);
    }
};

// Error handling
const errorHandler = {
    handleError: function(error, context = {}) {
        analytics.trackError(error, context);
        
        // Show user-friendly error message
        const errorMessage = document.getElementById('error-message');
        if (errorMessage) {
            errorMessage.textContent = this.getUserFriendlyMessage(error);
            errorMessage.style.display = 'block';
        }
    },
    
    getUserFriendlyMessage: function(error) {
        const errorMessages = {
            'card_error': 'There was an issue with your card. Please try again.',
            'validation_error': 'Please check your information and try again.',
            'rate_limit_error': 'Too many attempts. Please try again later.',
            'invalid_request_error': 'Something went wrong. Please try again.',
            'api_error': 'We\'re having trouble processing your request.',
            'default': 'An unexpected error occurred. Please try again.'
        };
        
        return errorMessages[error.type] || errorMessages.default;
    }
};

// Payment processing
const paymentProcessor = {
    async createCheckoutSession() {
        try {
            analytics.trackEvent('checkout_started');
            
            const response = await fetch('/api/create-checkout-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    priceId: 'price_H5ggYwtDq4fbrJ',
                    quantity: 1,
                    successUrl: window.location.origin + '/success',
                    cancelUrl: window.location.origin + '/cancel'
                })
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const session = await response.json();
            return session;
        } catch (error) {
            errorHandler.handleError(error, { context: 'createCheckoutSession' });
            throw error;
        }
    },
    
    async handleCheckout(session) {
        try {
            const result = await stripe.redirectToCheckout({
                sessionId: session.id
            });
            
            if (result.error) {
                throw result.error;
            }
            
            analytics.trackEvent('checkout_completed', {
                sessionId: session.id
            });
        } catch (error) {
            errorHandler.handleError(error, { context: 'handleCheckout' });
            throw error;
        }
    }
};

// UI Components
const uiComponents = {
    showLoading: function() {
        const button = document.getElementById('checkout-button');
        if (button) {
            button.disabled = true;
            button.textContent = 'Processing...';
        }
    },
    
    hideLoading: function() {
        const button = document.getElementById('checkout-button');
        if (button) {
            button.disabled = false;
            button.textContent = 'Buy Now';
        }
    },
    
    showError: function(message) {
        const errorDiv = document.getElementById('error-message');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
        }
    }
};

// Initialize checkout
document.addEventListener('DOMContentLoaded', function() {
    const checkoutButton = document.getElementById('checkout-button');
    if (checkoutButton) {
        checkoutButton.addEventListener('click', async function() {
            try {
                uiComponents.showLoading();
                const session = await paymentProcessor.createCheckoutSession();
                await paymentProcessor.handleCheckout(session);
            } catch (error) {
                uiComponents.showError(errorHandler.getUserFriendlyMessage(error));
            } finally {
                uiComponents.hideLoading();
            }
        });
    }
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        stripe,
        analytics,
        errorHandler,
        paymentProcessor,
        uiComponents
    };
} 