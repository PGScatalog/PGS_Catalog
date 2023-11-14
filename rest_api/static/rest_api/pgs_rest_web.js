$(window).bind("load", function () {
    var origin = window.location.origin;
    // Removing the external-link behaviour of internal links (pagination) within the JSON response block
    $('pre.prettyprint a[href^="'+origin+'"]').removeAttr('target').removeClass('external-link').addClass('internal-link');
  });