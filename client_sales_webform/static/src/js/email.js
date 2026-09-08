$(document).ready(function() {
    var forbiddenDomains = ['@gmail.com', '@yahoo.com', '@hotmail.com'];

    function getEmailError(email) {
        if (!email) {
            return 'Email is required';
        }

        for (var i = 0; i < forbiddenDomains.length; i++) {
            if (email.toLowerCase().includes(forbiddenDomains[i])) {
                return 'You must input your company email';
            }
        }

        return '';
    }

    // Realtime validation on input
    $('#email_from').on('input', function() {
        var email = $(this).val();
        var error = getEmailError(email);
        $('#email_error').html(error);
    });

    // Prevent submission if error exists
    $('form.o_website_form').submit(function(e) {
        var email = $('#email_from').val();
        var error = getEmailError(email);

        if (error) {
            $('#email_error').html(error);
            e.preventDefault();
        }
    });
});
