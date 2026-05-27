const gwas_rest_url = 'https://www.ebi.ac.uk/gwas/rest/api/v2/'

function get_gwas_study(gwas_id){
  return $.ajax({
        url: gwas_rest_url+'studies/'+encodeURIComponent(gwas_id),
        method: "GET",
        contentType: "application/json",
        dataType: 'json'
    })
}

function get_gwas_publication(pubmed_id){
  return $.ajax({
        url: gwas_rest_url+'publications/'+encodeURIComponent(pubmed_id),
        method: "GET",
        contentType: "application/json",
        dataType: 'json'
    })
}

$(document).ready(function() {
  const gwas_id = $('#gwas_id').text();
  if (gwas_id) {
    get_gwas_study(gwas_id)
    .done(function (data) {
      const ext_link = 'class="external-link" target="_blank"';

      // Description
      const data_desc = (data.initial_sample_size) ? data.initial_sample_size : '-';
      $('#gwas_desc').text(data_desc);
      // Trait
      const data_trait = (data.disease_trait) ? data.disease_trait : '-';
      $('#gwas_trait').text(data_trait);

      let pub_title = '-';
      let pub_author = '';
      let pub_date = '';
      let pub_journal = '';

      if (data.pubmed_id){
        const pubmed_id = data.pubmed_id;
        if (!/^\d+$/.test(pubmed_id)) {
            console.error('Unexpected pubmed_id format:', pubmed_id);
            return;
        }
        get_gwas_publication(pubmed_id)
            .done(function(data_pub){
              if (data_pub.title){
                pub_title = data_pub.title;
              }
              if (data_pub.first_author) {
                pub_author = data_pub.first_author.full_name;
              }
              if (data_pub.journal) {
                pub_journal = data_pub.journal;
              }
              if (data_pub.publication_date) {
                const date = data_pub.publication_date
                const date_list = date.split('-');

                if (date_list.length) {
                  const year = date_list[0];
                  pub_date = '('+year+')';
                } else {
                  pub_date = date;
                }
              }
            })
            .fail(function(){
              pub_title = 'Could not fetch publication information.'
            })
            .always(function(){
                // Building the publication information DOM
                $('#pub_loading').hide();

                // --- pub title ---
                $('#gwas_pub_title').text(pub_title);

                // --- pub info ---
                const $info = $('<span>');

                if (pub_author) {
                    $info.append(
                        $('<i>').addClass('fa fa-angle-double-right'),
                        ' ',
                        document.createTextNode(pub_author),
                        ' ',
                        $('<i>').text('et al.'),
                        ' '
                    );
                }
                if (pub_journal) {
                    $info.append(document.createTextNode(pub_journal + ' '));
                }
                if (pub_date) {
                    $info.append(document.createTextNode(pub_date));
                }

                // --- pubmed link ---
                const safe_pubmed_id = encodeURIComponent(pubmed_id);
                const $pubmedLink = $('<a>')
                    .attr('href', 'https://www.ncbi.nlm.nih.gov/pubmed/' + safe_pubmed_id)
                    .attr('target', '_blank')
                    .text('PMID:' + pubmed_id);

                const $pubmedSpan = $('<span>')
                    .addClass('pl-2 ml-2 pgs_v_separator_left')
                    .append($pubmedLink);

                $('#gwas_pub_info').empty().append($info, $pubmedSpan);

            })
      } else {
        $('#pub_loading').hide();
        $('#gwas_pub_title').html('No publication data');
      }
      const $link = $('<a>')
          .attr('class', 'external-link')
          .attr('target', '_blank')
          .attr('href', 'https://www.ebi.ac.uk/gwas/studies/' + gwas_id)
          .text('https://www.ebi.ac.uk/gwas/studies/' + gwas_id);
      $('#gwas_link').empty().append($link);

      const $pgs_loading = $('#pgs_loading');
      $pgs_loading.hide();
      $pgs_loading.html("");
      $('#gwas_table').show();
    })
    .fail(function (xhRequest, ErrorText, thrownError) {
      $('#pgs_loading').html('<h4><i class="fa fa-exclamation-triangle pgs_color_2 pr-3"></i>Error: we can\'t retrieve the NHGRI-EBI GWAS Catalog Study information at the moment</h4>');
    });
  }
  else {
    $('#pgs_loading').html('<h4><i class="fa fa-exclamation-triangle pgs_color_2 pr-3"></i>Error: can\'t find the GWAS ID</h4>');
  }
});
