/**
 * Ooredoo Qatar Clone - Payment Page JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // عداد الوقت المتبقي
    const countdownElement = document.querySelector('.countdown-text span');
    if (countdownElement) {
        let minutes = 9;
        let seconds = 32;
        
        const updateCountdown = () => {
            countdownElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            if (seconds === 0) {
                if (minutes === 0) {
                    // انتهى الوقت
                    clearInterval(countdownInterval);
                    return;
                }
                minutes--;
                seconds = 59;
            } else {
                seconds--;
            }
        };
        
        // تحديث العداد كل ثانية
        const countdownInterval = setInterval(updateCountdown, 1000);
    }
    // Format credit card number with spaces
    const cardNumberInput = document.getElementById('card_number');
    if (cardNumberInput) {
        cardNumberInput.addEventListener('input', function(e) {
            // Remove non-numeric characters
            let value = this.value.replace(/\D/g, '');
            
            // Limit to 16 digits
            if (value.length > 16) {
                value = value.slice(0, 16);
            }
            
            // Add space after every 4 digits
            const formattedValue = value.replace(/(\d{4})(?=\d)/g, '$1 ');
            
            this.value = formattedValue;
        });
    }

    // Format expiry date (MM/YY)
    const expiryDateInput = document.getElementById('expiry_date');
    if (expiryDateInput) {
        expiryDateInput.addEventListener('input', function(e) {
            // Remove non-numeric characters
            let value = this.value.replace(/\D/g, '');
            
            // Format as MM/YY
            if (value.length > 0) {
                // Get the month part (first 2 digits)
                let month = value.substring(0, 2);
                
                // Validate month (01-12)
                if (month.length === 2) {
                    const monthNum = parseInt(month, 10);
                    if (monthNum < 1) {
                        month = '01';
                    } else if (monthNum > 12) {
                        month = '12';
                    }
                }
                
                // Format with slash if we have more than 2 digits
                if (value.length > 2) {
                    this.value = month + '/' + value.substring(2, 4);
                } else {
                    this.value = month;
                }
            }
            
            // Limit to 5 characters (MM/YY)
            if (this.value.length > 5) {
                this.value = this.value.slice(0, 5);
            }
        });
    }

    // Format CVV (3 digits)
    const cvvInput = document.getElementById('cvv');
    if (cvvInput) {
        cvvInput.addEventListener('input', function(e) {
            // Remove non-numeric characters
            this.value = this.value.replace(/\D/g, '');
            
            // Limit to 3 digits
            if (this.value.length > 3) {
                this.value = this.value.slice(0, 3);
            }
        });
    }

    // Payment form validation
    const paymentForm = document.getElementById('payment-form');
    if (paymentForm) {
        paymentForm.addEventListener('submit', function(e) {
            let isValid = true;
            
            // Card number validation
            const cardNumber = cardNumberInput.value.replace(/\s/g, '');
            if (cardNumber.length !== 16) {
                isValid = false;
                showError(cardNumberInput, 'يجب أن يتكون رقم البطاقة من 16 رقم');
            } else {
                hideError(cardNumberInput);
            }
            
            // Expiry date validation
            const expiryDate = expiryDateInput.value;
            if (!expiryDate.match(/^\d{2}\/\d{2}$/)) {
                isValid = false;
                showError(expiryDateInput, 'يرجى إدخال تاريخ الانتهاء بالصيغة التالية: MM/YY');
            } else {
                // Check if the expiry date is valid (not expired)
                const [month, year] = expiryDate.split('/');
                const expiryMonth = parseInt(month, 10);
                const expiryYear = parseInt('20' + year, 10);
                
                const now = new Date();
                const currentMonth = now.getMonth() + 1;
                const currentYear = now.getFullYear();
                
                if (expiryYear < currentYear || (expiryYear === currentYear && expiryMonth < currentMonth)) {
                    isValid = false;
                    showError(expiryDateInput, 'البطاقة منتهية الصلاحية');
                } else {
                    hideError(expiryDateInput);
                }
            }
            
            // CVV validation
            if (cvvInput.value.length !== 3) {
                isValid = false;
                showError(cvvInput, 'يجب أن يتكون رمز الأمان من 3 أرقام');
            } else {
                hideError(cvvInput);
            }
            
            // Cardholder name validation
            const cardholderNameInput = document.getElementById('cardholder_name');
            if (cardholderNameInput.value.trim() === '') {
                isValid = false;
                showError(cardholderNameInput, 'يرجى إدخال اسم حامل البطاقة');
            } else {
                hideError(cardholderNameInput);
            }
            
            // If not valid, prevent form submission
            if (!isValid) {
                e.preventDefault();
            }
        });
    }

    // Helper functions for form validation
    function showError(inputElement, errorMessage) {
        // Remove existing error message if any
        const existingError = inputElement.nextElementSibling;
        if (existingError && existingError.classList.contains('invalid-feedback')) {
            existingError.remove();
        }
        
        // Add error class to input
        inputElement.classList.add('is-invalid');
        
        // Create error message element
        const errorElement = document.createElement('div');
        errorElement.className = 'invalid-feedback d-block';
        errorElement.textContent = errorMessage;
        
        // Add error message after input
        inputElement.parentNode.insertBefore(errorElement, inputElement.nextSibling);
    }

    function hideError(inputElement) {
        // Remove error class from input
        inputElement.classList.remove('is-invalid');
        
        // Remove error message if any
        const errorElement = inputElement.nextElementSibling;
        if (errorElement && errorElement.classList.contains('invalid-feedback')) {
            errorElement.remove();
        }
    }
});
