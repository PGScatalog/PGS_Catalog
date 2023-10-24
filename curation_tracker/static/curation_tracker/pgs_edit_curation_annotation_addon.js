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

function toggleAuthorSub(){
    var isAuthorSub = $('#id_author_submission').is(":checked");
    var study_name = $('#id_study_name').val();
    if(study_name){
        if(isAuthorSub){
            var author_year = study_name.split('_')[0];
            $('#id_study_name').val(author_year+'_AuthorSub');
        } else {
            $('#id_study_name').val(study_name.replace(/_AuthorSub/g,''));
        }
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
                if(publicationData.hasOwnProperty('firstPublicationDate')){
                    $('#id_publication_date').val(publicationData.firstPublicationDate);
                }
                if(!$('#id_study_name').val() && publicationData.hasOwnProperty('authorString') && publicationData.hasOwnProperty('pubYear')){
                    var study_name = publicationData.authorString.split(' ')[0] + publicationData.pubYear;
                    $('#id_study_name').val(study_name);
                    toggleAuthorSub();
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
    // Adding 'go to publication' and 'Autofill' buttons after the DOI and PMID form fields 
    $('div.form-row.field-doi.field-PMID > div.flex-container').append('<div><div><a title="Go to the publication page using DOI or the Pubmed page if only the PMID is provided" href="" class="extra-field-button external-link" onclick="goToPublication(); return false;">Go to publication</a></div><div style="display: flex;"><div><a title="Fetch the publication data from EPMC and fill in the form automatically (DOI or PMID required)" href="" class="extra-field-button" onclick="autofillForm(); return false;">Autofill <i class="fa-solid fa-gears"></i></a></div><div id="doi_pmid_error" class="fieldBox errors"><ul class="errorlist"></ul></div></div></div>');

    // Adding toggle AuthorSub suffix function
    $('#id_author_submission').click(toggleAuthorSub);
})