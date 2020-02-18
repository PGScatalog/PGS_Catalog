$(document).ready(function() {

    // Fix issue with internal links because of the sticky header
    function offsetAnchor() {
      if(location.hash.length !== 0) {
        window.scrollTo(window.scrollX, window.scrollY - 95);
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


    function shorten_displayed_content() {
      $('.more').each(function() {
          var content = $(this).html();
          if(content.length > showChar) {
              var c = content.substr(0, showChar);
              var h = content.substr(showChar, content.length - showChar);
              var html = c + '<span class="moreellipses">' + ellipsestext+ '&nbsp;</span><span class="morecontent"><span>' + h + '</span>&nbsp;&nbsp;<a href="" class="morelink link_more">' + moretext + '</a></span>';
              $(this).html(html);
          }
      });
    }
    shorten_displayed_content();


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
      $(this).find('i').toggleClass("fa-plus-circle fa-minus-circle");
      id = $(this).attr('id');
      $('#list_'+id).toggle();
    });

    // Button toggle within an HTML table
    $('table.table[data-toggle="table"]').on("click", ".toggle_table_btn", function(){
      pgs_tooltip();
      $(this).find('i').toggleClass("fa-plus-circle fa-minus-circle");
      id = $(this).attr('id');
      $('#list_'+id).toggle();
    });

    $('table.table[data-toggle="table"]').on("click", ".sortable", function(){
      setTimeout(function(){
        alter_external_links('table.table[data-toggle="table"] tbody');
        shorten_displayed_content();
      }, 0);
    });
    var timer;
    var timeout = 1000;
    $('.form-control').keyup(function(){
      clearTimeout(timer);
      if ($('.form-control').val) {
          timer = setTimeout(function(){
            alter_external_links('table.table[data-toggle="table"] tbody');
            shorten_displayed_content();
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

    // Remove pagination text if there is no pagination links
    $('.fixed-table-pagination').each(function(index) {
      console.log("Class found #"+index+"!");
      var page_list = $( this ).find('.page-list');
      if (page_list.length == 0) {
        $( this ).remove();
      }
      else {
        if (page_list.css('display') == 'none') {
          $( this ).remove();
        }
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
          var pgs_param_sup = pgs_param.replace(chars+matches[i], chars+"<sup>"+matches[i]+"</sup>");
          $('#pgs_params').html(pgs_param_sup);
          pgs_param = pgs_param_sup;
        }
      }
      // Update rsquare notation (r2)
      $('#pgs_params').html(pgs_param.replace("r2", "r<sup>2</sup>"));
    }
});


/*
 * Functions to display the trait category piechart and the different trait
 * categories and traits boxes.
 */

function reset_showhide_trait() {
  // Reset traits
  $('.trait_subcat_container').hide("slow");
  // Reset button
  $('#reset_cat').hide("slow");
  // Reset search
  add_search_term('');
}

function fadeIn(elem) {
  elem.css('opacity', 0);
  elem.css('display', 'block');

  var op = 0.1;  // opacity step

  // Fade in the elem (fadeIn() is not included in the slim version of jQuery)
  var timer = setInterval(function () {
    if (op >= 1){
      clearInterval(timer);
    }
    elem.css('opacity', op);
    elem.css('filter', 'alpha(opacity=' + op * 100 + ")");
    op += op * 0.1;
  }, 15);
}

function showhide_trait(id, term) {
  var elem = $('#'+id);

  if (!elem.is(':visible')) {
    // Hide previously selected traits
    $('.trait_subcat_container').hide();

    // Display list of traits
    fadeIn(elem);

    // Add search term to filter the table
    add_search_term(term);

    // Reset button
    $('#reset_cat').show("slow");
  }

  $('a.trait_item').mouseover(function() {
    trait_link = $(this).find('.trait_link');
    if (trait_link.length == 0) {
      $(this).append('<i class="icon icon-common trait_link" data-icon="&#xf0c1;"></i>');
    }
    else {
      trait_link.show();
    }
  });
  $('a.trait_item').mouseout(function() {
    $(this).find('.trait_link').hide();
  });
}


function add_search_term(term) {
  var elems = $('.search-input');
  if (elems.length > 0) {
    elem = elems[0];
    elem.focus();
    elem.value = term;
    elem.blur();
    setTimeout(function(){
      $('table.table[data-toggle="table"] tbody a[href^="http"]').attr('target','_blank');
      $('table.table[data-toggle="table"] tbody a[href^="http"]').not('[class*="pgs_no_icon_link"]').addClass("external-link");
    }, 1000);
  }
}


// Build and draw the Trait category piechart
function draw_trait_category_piechart(data_chart) {

  var labels_list = [];
  var bg_list = [];
  var count_list = [];

  $.each(data_chart, function(index, data) {
    labels_list.push(data.name);
    bg_list.push(data.colour);
    count_list.push(data.size_g);
  });

  var chart_element = document.getElementById("trait_cat_piechart");
  new Chart(chart_element, {
    type: 'doughnut',
    data: {
      labels: labels_list,
      datasets: [{
        label: "PGS Scores per trait category",
        backgroundColor: bg_list,
        data: count_list
      }]
    },
    options: {
      title: {
        display: false
      },
      legend: {
        display: false
      },
      responsive: true,
      'onClick' : function (evt, item) {
        if (item[0]) {
          var index = item[0]['_index'];
          showhide_trait(data_chart[index].id+"_list", labels_list[index]);

        }
      },
      hover: {
        onHover: function(e, el) {
          $("#trait_cat_piechart").css("cursor", el[0] ? "pointer" : "default");
        }
      }
    }
  });
}


function display_category_list(data_json) {
  var trait_elem = document.getElementById("trait_cat");
  var subtrait_elem = document.getElementById("trait_subcat");

  item_height = 35;
  number_of_cat = Object.keys(data_json).length;

  cat_div_height = number_of_cat * item_height;
  cat_div_height += 'px';

  category_tooltip = 'data-toggle="tooltip" title=""';
  colour_to_replace = '##COLOUR##';
  colour_box = '<span class="trait_colour" style="background-color:'+colour_to_replace+'"></span>';
  count_to_replace = '##COUNT##';
  count_badge = '<span class="badge badge-pill badge-pgs float_right">'+count_to_replace+' <span>PGS</span></span>';
  category_arrow = '<i class="icon icon-common" data-icon="&#xf061;"></i>';

  for (cat_index in data_json) {
    cat_index = parseInt(cat_index);

    var name     = data_json[cat_index].name;
    var div_id   = data_json[cat_index].id+"_list";
    var t_colour = data_json[cat_index].colour;
    var size_g   = data_json[cat_index].size_g;

    // Get an idea if the colour is quite light. If so, it will outline the arrow
    colour_light = t_colour.match(/^#(\w)\w(\w)\w(\w)/);
    count_nb_f = 0
    for (var i=1;i<4;i++) {
      if (colour_light[i] == 'F' || colour_light[i] == 'f') {
        count_nb_f++;
      }
    }

    var colour_span = colour_box.replace(colour_to_replace,t_colour);
    if (count_nb_f > 1) {
      colour_span = colour_span.replace('trait_colour','trait_colour trait_colour_border');
    }

    // Create category box
    var e = document.createElement('div');
    e.className = "trait_item";
    e.innerHTML = colour_span+'<span>'+name+'</span>'+count_badge.replace(count_to_replace,size_g);
    e.setAttribute("data-toggle", "tooltip");
    e.setAttribute("data-placement", "left");
    e.setAttribute("data-delay", "800");
    e.setAttribute("title", "Click to display the list of traits related to '"+name+"'");
    e.setAttribute("onclick", "showhide_trait('"+div_id+"', '"+name+"')");
    trait_elem.appendChild(e);


    // Create sub-categories (traits) main container
    subcat_children = data_json[cat_index].children;
    var se = document.createElement('div');
    se.id = div_id;
    se.className = "trait_subcat_container clearfix";
    se.style.display = "none";

    // Arrow separator - vertical position
    var se_left = document.createElement('div');
    var class_name = (count_nb_f>1) ? 'trait_subcat_left trait_subcat_border' : 'trait_subcat_left';
    se_left.className = class_name;
    se_left.style.color = t_colour;
    se_left.innerHTML = category_arrow;
    var subcat_div_height_left = cat_index * item_height;
    se_left.style.marginTop = subcat_div_height_left+"px";
    se.appendChild(se_left);

    // Sub-categories (traits) sub container - vertical position
    var se_right = document.createElement('div');
    se_right.className = "trait_subcat_right";

    var subcat_div_height_right = 0;
    var count = cat_index + (subcat_children.length/2);

    if (subcat_children.length == 1) {
      subcat_div_height_right = cat_index * item_height;
    }
    else if (cat_index == number_of_cat-1) {
      cat_pos = cat_index * item_height;

      if (subcat_children.length < number_of_cat) {
        subcat_div_height_right = (number_of_cat -subcat_children.length)*item_height;
      }
    }
    else if ((cat_index + (subcat_children.length/2)) < number_of_cat) {
      cat_pos = cat_index * item_height;
      subcat_div_height_right = cat_pos - ((subcat_children.length)*item_height)/2 + item_height/2;
    }

    // Display scrollbar for categories with lots of traits
    if (subcat_children.length > number_of_cat) {
      se_right.style.maxHeight = cat_div_height;
      se_right.classList.add("v-scroll");
    }

    se_right.style.marginTop = subcat_div_height_right+"px";

    // Create the sub-categories (traits) boxes
    for (subcat_index in subcat_children) {
      var sc_id   = subcat_children[subcat_index].id;
      var sc_name = subcat_children[subcat_index].name;
      var sc_size = subcat_children[subcat_index].size;
      var sc = document.createElement('a');
      sc.className = "trait_item";
      sc.innerHTML = colour_span+'<span>'+sc_name+'</span>'+count_badge.replace(count_to_replace,sc_size);
      sc.setAttribute("href", "/trait/"+sc_id);
      sc.setAttribute("data-toggle", "tooltip");
      sc.setAttribute("data-placement", "left");
      sc.setAttribute("data-delay", "800");
      sc.setAttribute("title", "Click to go to the detailed page of the '"+sc_name+"' trait");
      se_right.appendChild(sc);
    }
    se.appendChild(se_right);

    subtrait_elem.appendChild(se);
  }

  // Display list of trait categories
  fadeIn($("#trait_cat"));
}


// Build and draw sample distribution piecharts
function draw_samples_piechart(data_chart, id, type) {

  var pc_class   = (type == 'sample') ? "sample_piechart_" : "sample_piechart_gender_";
  var pc_colours = (type == 'sample') ? ["#3e95cd", "#8e5ea2"] : ["#F18F2B", "#4F78A7"];
  var pc_title   = (type == 'sample') ? 'Sample distribution' : 'Sample gender distribution';

  new Chart(document.getElementById(pc_class+id), {
    type: 'doughnut',
    data: {
      labels: data_chart[0],
      datasets: [{
        backgroundColor: pc_colours,
        data: data_chart[1]
      }]
    },
    options: {
      title: {
        display: true,
        text: pc_title
      },
      legend: {
        position: 'bottom',
        reverse: true,
        labels: {
          boxWidth: 20
        }
      }
    }
  });
}
