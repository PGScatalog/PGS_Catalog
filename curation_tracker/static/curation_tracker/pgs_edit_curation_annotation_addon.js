const $ = django.jQuery;

function setError(error){
    var errorList = $('div#doi_pmid_error > ul.errorlist')
    if(error){
        errorList.append('<li>'+error+'</li>');
    } else {
        errorList.empty();
    }
}

function goToPGP(event){
    var new_window = event.data.new_window;
    setError('');
    var pgp_id = $('#id_pgp_id').val();
    if(pgp_id){
        var url = '/publication/'+pgp_id;
        if(new_window){
            window.open(url);
        } else {
            window.location = url;
        }
    } else {
        alert('Please provide a PGP ID first');
    }
    return false; // To avoid reloading the current page
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
    return false; // To avoid reloading the current page
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

function _fillFormWithInfo(publicationData){
    if(publicationData.hasOwnProperty('doi')){
        $('#id_doi').val(publicationData.doi);
    }
    if(publicationData.hasOwnProperty('pmid')){
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
}

function _getPublicationInfo({doi=null, pmid=null}){
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
            if(data.hitCount > 0){
                var publicationData = data.resultList.result[0];
                _fillFormWithInfo(publicationData);
            } else {
                if(doi && pmid){
                    // Try again just with PMID (some publications return results only with PMID)
                    _getPublicationInfo({doi: null, pmid:pmid});
                } else {
                    setError('No result found in Europe PMC');
                }
            }
        } else {
            setError('EMPC Server error');
        }
    }).fail(function(error){
        setError('EMPC Server error: '+error.statusText);
    })
}

function autofillForm(){
    setError('');
    var doi = $('#id_doi').val();
    var pmid = $('#id_PMID').val();
    _getPublicationInfo({doi: doi, pmid: pmid});
    return false; // To avoid reloading the current page
}

function requestAuthorData(){
    $.get('../contact-author/', function(data,status){
        if(status == 'success'){
            if(data.error){
                alert(data.error);
            } else {
                var email_subject = encodeURIComponent(data.email_subject);
                var email_body = encodeURIComponent(data.email_body);
                var cc = encodeURIComponent(data.cc);
                window.open('mailto:'+'?subject='+email_subject+'&body='+email_body+'&cc='+cc);
            }
        } else {
            alert('Error');
            console.error(data);
        }
    }).fail(function(error){
        console.error(error);
        alert('Error: '+error.statusText);
    })
    return false;
}

$(document).ready(function(){
    // Adding 'go to PGS Catalog publication' button after the PGP id field
    var pgp_id_div = $('div.form-row.field-pgp_id > div');
    pgp_id_div.addClass('flex-container');
    pgp_id_div.find(">:first-child").addClass('fieldBox');
    pgp_id_div.append('<div><a id="go_to_pgp_link" title="Go to the PGS Catalog curation publication page" href="" class="extra-field-button external-link">Go to PGS Catalog publication</a></div>');

    // Adding 'go to publication' and 'Autofill' buttons after the DOI and PMID form fields 
    $('div.form-row.field-doi.field-PMID > div.flex-container').append('<div><div><a id="go_to_publication_link" title="Go to the publication page using DOI or the Pubmed page if only the PMID is provided" href="" class="extra-field-button external-link">Go to publication</a></div><div style="display: flex;"><div><a id="autofill_link" title="Fetch the publication data from EPMC and fill in the form automatically (DOI or PMID required)" href="" class="extra-field-button">Autofill <i class="fa-solid fa-gears"></i></a></div><div id="doi_pmid_error" class="fieldBox errors"><ul class="errorlist"></ul></div></div></div>');

    // Adding actions to the buttons
    var pgp_link_selector = $('#go_to_pgp_link')
    pgp_link_selector.click({'new_window': false}, goToPGP);
    pgp_link_selector.on('auxclick', {'new_window': true}, goToPGP);
    $('#go_to_publication_link').click(goToPublication);
    $('#autofill_link').click(autofillForm);

    // Adding toggle AuthorSub suffix function
    $('#id_author_submission').click(toggleAuthorSub);

    // Request Author Data button
    $('#request_author_data_button').click(requestAuthorData);
})