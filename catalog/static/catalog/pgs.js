$(document).ready(function() {

    // Fix issue with internal links because of the sticky header
    function offsetAnchor() {
      if(location.hash.length !== 0) {
        window.scrollTo(window.scrollX, window.scrollY - 105);
      }
    }
    // This will capture hash changes while on the page
    $(window).on("hashchange",offsetAnchor);
    // This is here so that when you enter the page with a hash,
    // it can provide the offset in that case too. Having a timeout
    // seems necessary to allow the browser to jump to the anchor first.
    window.setTimeout(offsetAnchor, 0.1);


    // Configure/customize these variables.
    var showChar = 100;  // How many characters are shown by default
    var ellipsestext = "...";
    var moretext = 'Show more';
    var lesstext = 'Show less';

    $('.more').each(function() {
        var content = $(this).html();
        if(content.length > showChar) {
            var c = content.substr(0, showChar);
            var h = content.substr(showChar, content.length - showChar);
            var html = c + '<span class="moreellipses">' + ellipsestext+ '&nbsp;</span><span class="morecontent"><span>' + h + '</span>&nbsp;&nbsp;<a href="" class="morelink link_more">' + moretext + '</a></span>';
            $(this).html(html);
        }
    });

    $(".morelink").click(function(){
        if($(this).hasClass("link_less")) {
          $(this).html(moretext);
        } else if ($(this).hasClass("link_more")){
          $(this).html(lesstext);
        }
        $(this).toggleClass("link_less link_more");
        // Show/hide "..." characters
        $(this).parent().prev().toggle();
        // Show/hide the rest of the text
        $(this).prev().toggle();
        return false;
    });
    /*$("#myInput").on("keyup", function() {
        var value = $(this).val().toLowerCase();
        $("#filterableTable tr").filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    });*/


    // Add external link icon and taget blank for external links
    function alter_external_links(prefix) {
      if (!prefix) {
        prefix = '';
      }
      else {
        prefix += ' '
      }
      $(prefix+'a[href^="http"]').attr('target','_blank');
      $(prefix+'a[href^="http"]').not('[class*="pgs_no_icon_link"]').addClass("external-link");
    }
    alter_external_links();

    // Tooltip | Popover
    function pgs_tooltip() {
      $('.pgs_helptip').attr('data-toggle','tooltip').attr('data-placement','bottom');
      $('.pgs_helpover').attr('data-toggle','popover').attr('data-placement','bottom');

      $('[data-toggle="tooltip"]').tooltip();
      $('[data-toggle="popover"]').popover();
    }
    pgs_tooltip();

    // EMBL-EBI Data Protection banner
    var localFrameworkVersion = '1.3'; // 1.1 or 1.2 or compliance or other
    // if you select compliance or other we will add some helpful
    // CSS styling, but you may need to add some CSS yourself
    var newDataProtectionNotificationBanner = document.createElement('script');
    newDataProtectionNotificationBanner.src = 'https://ebi.emblstatic.net/web_guidelines/EBI-Framework/v'+localFrameworkVersion+'/js/ebi-global-includes/script/5_ebiFrameworkNotificationBanner.js?legacyRequest='+localFrameworkVersion;
    document.head.appendChild(newDataProtectionNotificationBanner);
    newDataProtectionNotificationBanner.onload = function() {
      ebiFrameworkRunDataProtectionBanner(localFrameworkVersion); // invoke the banner
    };

    // Button toggle
    $('.toggle_btn').click(function() {
      $(this).find('i').toggleClass("icon-plus-square icon-minus-square");
      id = $(this).attr('id');
      $('#list_'+id).toggle();
    });

    // Button toggle within an HTML table
    $('table.table[data-toggle="table"]').on("click", ".toggle_table_btn", function(){
      pgs_tooltip();
      $(this).find('i').toggleClass("icon-plus-square icon-minus-square");
      id = $(this).attr('id');
      $('#list_'+id).toggle();
    });

    $('table.table[data-toggle="table"]').on("click", ".sortable", function(){
      setTimeout(function(){
        alter_external_links('table.table[data-toggle="table"] tbody');
      }, 0);
    });
    var timer;
    var timeout = 1000;
    $('.form-control').keyup(function(){
      clearTimeout(timer);
      if ($('.form-control').val) {
          timer = setTimeout(function(){
            alter_external_links('table.table[data-toggle="table"] tbody');
          }, timeout);
      }
    });

    // Remove column search if the number of rows is too small
    $('table.table[data-toggle="table"]').each(function(index) {
      var trs = $( this ).find( "tbody > tr");
      if (trs.length < 3) {
        $( this ).find('.fht-cell').hide()
      }
    });

    // Update to the scientific notation (1x10-1 and 1e-1)
    if ($('#pgs_params').length) {
      var pgs_param = $('#pgs_params').html();
      var matches = pgs_param.match(/\d+(x10|e)(-?\d+)/);
      if (matches && matches.length > 2) {
        for(var i=2; i<matches.length; i++) {
          if (matches[i] == 'x10' || matches[i] == 'e') {
            continue;
          }
          var chars = (matches[i-1] == 'x10') ? 'x10' : 'e';
          let pgs_param_sup = pgs_param.replace(chars+matches[i], chars+"<sup>"+matches[i]+"</sup>");
          $('#pgs_params').html(pgs_param_sup);
          pgs_param = pgs_param_sup;
        }
      }
      // Update rsquare notation (r2)
      $('#pgs_params').html(pgs_param.replace("r2", "r<sup>2</sup>"));
    }

});
