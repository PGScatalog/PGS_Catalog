document.addEventListener('DOMContentLoaded', function() {
    // Add history.back() function to all cancel buttons
    const cancelButtons = document.querySelectorAll('.pgs-admin-cancel');
    cancelButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            history.back();
        });
    });
});