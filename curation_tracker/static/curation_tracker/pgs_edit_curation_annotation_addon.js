const $ = django.jQuery;

function setError(error){
    var errorList = $('div#doi_pmid_error > ul.errorlist')
    if(error){
        errorList.append('<li>'+error+'</li>');
    } else {
        errorList.empty();
    }
}

function goToPublication(){
    setError('');
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

function autofillForm(){
    setError('');
    var doi = $('#id_doi').val();
    var pmid = $('#id_PMID').val();
    var baseUrl = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&query='
    var url;
    if(doi){
        url = baseUrl + 'doi:' + doi;
    } else if(pmid){
        url = baseUrl + 'ext_id:' + pmid;
    } else {
        setError('Please provide a DOI or PubMed ID');
        return;
    }
    $.get(url,function(data, status){
        if(status == 'success'){
            var publicationData = data.resultList.result[0];
            if(publicationData){
                if(!doi && publicationData.hasOwnProperty('doi')){
                    $('#id_doi').val(publicationData.doi);
                }
                if(!pmid && publicationData.hasOwnProperty('pmid')){
                    $('#id_PMID').val(publicationData.pmid);
                }
                if(publicationData.hasOwnProperty('title')){
                    $('#id_title').val(publicationData.title);
                }
                if(publicationData.hasOwnProperty('journalTitle')){
                    $('#id_journal').val(publicationData.journalTitle);
                }
                if(publicationData.hasOwnProperty('pubYear')){
                    $('#id_year').val(publicationData.pubYear);
                }
                if(!$('#id_study_name').val() && publicationData.hasOwnProperty('authorString') && publicationData.hasOwnProperty('pubYear')){
                    var study_name = publicationData.authorString.split(' ')[0] + publicationData.pubYear;
                    $('#id_study_name').val(study_name);
                }
            } else {
                setError('No result found in Europe PMC');
            }
        } else {
            setError('EMPC Server error');
        }
    }).fail(function(error){
        setError('EMPC Server error: '+error.statusText);
    })
}

$(document).ready(function(){
    // Adding a 'go to publication' button after the DOI and PMID form fields
    var doi_pmid_div = $('div.form-row.field-doi.field-PMID');
    doi_pmid_div.append('<div><a href="" class="extra-field-button external-link" onclick="goToPublication(); return false;">Go to publication</a></div>');
    // Adding a 'Autofill' button
    doi_pmid_div.append('<div style="display: flex;"><div><a href="" class="extra-field-button" onclick="autofillForm(); return false;">Autofill <i class="fa-solid fa-gears"></i></a></div><div id="doi_pmid_error" class="fieldBox errors"><ul class="errorlist"></ul></div></div>');
})