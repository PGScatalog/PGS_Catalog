const $ = django.jQuery;

function goToPublication(){
    var doi = $('#id_doi').val();
    var pmid = $('#id_PMID').val();
    if(doi){
        window.open('https://doi.org/'+doi,'_blank');
    } else if(pmid){
        window.open('https://pubmed.ncbi.nlm.nih.gov/'+pmid,'_blank');
    } else {
        alert('Please provide a DOI or PubMed ID');
    }
}

$(document).ready(function(){
    // Adding a 'go to publication' button after the DOI and PMID form fields
    $('div.form-row.field-doi.field-PMID').append('<div><a href="" class="extra-field-button external-link" onclick="goToPublication(); return false;">Go to publication</a></div>');
})