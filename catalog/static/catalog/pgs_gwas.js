var gwas_rest_url = 'https://www.ebi.ac.uk/gwas/rest/api/studies/'

$(document).ready(function() {
  var gwas_id = $('#gwas_id').html();
  if (gwas_id) {
    $.ajax({
        url: gwas_rest_url+gwas_id,
        method: "GET",
        contentType: "application/json",
        dataType: 'json'
    })
    .done(function (data) {
      var ext_link = 'class="external-link" target="_blank"';

      // Description
      var data_desc = (data.initialSampleSize) ? data.initialSampleSize : '-';
      $('#gwas_desc').html(data_desc);
      // Trait
      var data_trait = (data.diseaseTrait) ? data.diseaseTrait.trait : '-';
      $('#gwas_trait').html(data_trait);

      var pub_title = '-';
      var pub_author = '';
      var pubmed_id = '';
      var pub_date = '';
      var pub_journal = '';
      if (data.publicationInfo) {
        data_pub = data.publicationInfo;
        if (data_pub.title) {
          pub_title = data_pub.title;
        }
        if (data_pub.author) {
          pub_author = '<i class="fa fa-angle-double-right"></i> '+data_pub.author.fullname+' <i>et al.</i> ';
        }
        if (data_pub.publication) {
          pub_journal = data_pub.publication;
        }
        if (data_pub.publicationDate) {
          date = data_pub.publicationDate
          date_list = date.split('-');

          if (date_list.length) {
            date = date_list[0]
          }
          pub_date = '('+date+')';
        }
        if (data_pub.pubmedId) {
          pubmed_id = '<span class="pl-2 ml-2 pgs_v_separator_left"><a '+ext_link+' href="https://www.ncbi.nlm.nih.gov/pubmed/'+data_pub.pubmedId+'">PMID:'+data_pub.pubmedId+'</a></span>';
        }
      }
      $('#gwas_pub_title').html(pub_title);
      $('#gwas_pub_info').html('<span>'+pub_author+' '+pub_journal+' '+pub_date+'</span>'+pubmed_id);
      $('#gwas_link').html('<a '+ext_link+' href="https://www.ebi.ac.uk/gwas/studies/'+gwas_id+'">https://www.ebi.ac.uk/gwas/studies/'+gwas_id+'</a>');

      $('#pgs_loading').hide();
      $('#pgs_loading').html("");
      $('#gwas_table').show();
    })
    .fail(function (xhRequest, ErrorText, thrownError) {
      $('#pgs_loading').html('<h4><i class="fa fa-exclamation-triangle pgs_color_2 pr-3"></i>Error: we can\'t retrieve the NCBI-EBI GWAS Catalog Study information at the moment</h4>');
    });
  }
  else {
    $('#pgs_loading').html('<h4><i class="fa fa-exclamation-triangle pgs_color_2 pr-3"></i>Error: can\'t find the GWAS ID</h4>');
  }
});
