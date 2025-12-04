const gwas_rest_url = 'https://www.ebi.ac.uk/gwas/rest/api/v2/'

function get_gwas_study(gwas_id){
  return $.ajax({
        url: gwas_rest_url+'studies/'+gwas_id,
        method: "GET",
        contentType: "application/json",
        dataType: 'json'
    })
}

function get_gwas_publication(pubmed_id){
  return $.ajax({
        url: gwas_rest_url+'publications/'+pubmed_id,
        method: "GET",
        contentType: "application/json",
        dataType: 'json'
    })
}

$(document).ready(function() {
  var gwas_id = $('#gwas_id').html();
  if (gwas_id) {
    get_gwas_study(gwas_id)
    .done(function (data) {
      var ext_link = 'class="external-link" target="_blank"';

      // Description
      const data_desc = (data.initial_sample_size) ? data.initial_sample_size : '-';
      $('#gwas_desc').html(data_desc);
      // Trait
      const data_trait = (data.disease_trait) ? data.disease_trait : '-';
      $('#gwas_trait').html(data_trait);

      let pub_title = '-';
      let pub_author = '';
      let pub_date = '';
      let pub_journal = '';

      if (data.pubmed_id){
        const pubmed_id = data.pubmed_id;
        get_gwas_publication(pubmed_id)
            .done(function(data_pub){
              if (data_pub.title){
                pub_title = data_pub.title;
              }
              if (data_pub.first_author) {
                pub_author = '<i class="fa fa-angle-double-right"></i> '+data_pub.first_author.full_name+' <i>et al.</i> ';
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
              $('#pub_loading').hide();
              const pubmed_id_html = '<span class="pl-2 ml-2 pgs_v_separator_left"><a '+ext_link+' href="https://www.ncbi.nlm.nih.gov/pubmed/'+pubmed_id+'">PMID:'+pubmed_id+'</a></span>';
              $('#gwas_pub_title').html(pub_title);
              $('#gwas_pub_info').html('<span>'+pub_author+' '+pub_journal+' '+pub_date+'</span>'+pubmed_id_html);

            })
      } else {
        $('#pub_loading').hide();
        $('#gwas_pub_title').html('No publication data');
      }
      $('#gwas_link').html('<a '+ext_link+' href="https://www.ebi.ac.uk/gwas/studies/'+gwas_id+'">https://www.ebi.ac.uk/gwas/studies/'+gwas_id+'</a>');
      $('#pgs_loading').hide();
      $('#pgs_loading').html("");
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
