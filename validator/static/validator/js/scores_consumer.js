const pyworker = await import((on_gae)?'./py-worker.min.js':'./py-worker.js');
const asyncRun = pyworker.asyncRun;

const validate_scores = await fetch(new URL('../python/bin/validation_scores.py', import.meta.url, null)).then(response => response.text());

let dirHandle;
let webkitFiles;
let validateFileHandle;

const MAX_ERRORS_PER_FILE = 50;

function successMount(dirName){
    document.getElementById('grant_message').innerHTML = 'Authorization granted on directory \"'+dirName+"\".";
}

async function mountLocalDirectory() {
    // use the same ID crypt4gh to open pickers in the same directory
    dirHandle = await showDirectoryPicker();

    if ((await dirHandle.queryPermission({ mode: "read" })) !== "granted") {
        if (
            (await dirHandle.requestPermission({ mode: "read" })) !== "granted"
        ) {
            throw Error("Unable to read and write directory");
        }
    }
    return dirHandle;
}

function report_items_2_html(messages) {
    let report = '<ul>';
    $.each(messages, function(index, message){
      report += "<li>"+message+"</li>";
    });
    report += '</ul>';
    return report;
}

/** Class responsible on injecting report HTML code into the output div of the template. */
class ScoreReport {
    constructor(score_name) {
        let validation_output_div = $("#validation_out");
        this.status_icon = $("<i title=\"Queuing\" class=\"fa fa-clock\"></i>"); // Queuing status
        this.root_node = $("<div></div>");
        this.title = $("<h5 class=\"mt-4\">"+score_name+" </h5>");
        this.title.append(this.status_icon);
        this.root_node.append(this.title);
        validation_output_div.append(this.root_node);
    }

    set_status_validating(){
        this.status_icon.removeClass();
        this.status_icon.addClass("spinner-border spinner-border-sm pgs_color_1");
        this.status_icon.prop("title", "Validating...");
    }

    set_status_valid(){
        this.status_icon.removeClass();
        this.status_icon.addClass("fa fa-check-circle pgs_color_green");
        this.status_icon.prop("title", "Valid");
    }

    set_status_invalid(){
        this.status_icon.removeClass();
        this.status_icon.addClass("fa fa-times-circle pgs_color_red");
        this.status_icon.prop("title", "Not valid");
    }

    addReportTable(scoring_file_errors, items_header) {
        let table_html = '<table class="table table-bordered" style="width:auto"><thead class="thead-light">' +
            '<tr><th>Row</th><th>' + items_header + '</th></tr>' +
            '</thead><tbody>';
        // Looping through the errors up the maximum allowed
        for(let i = 0 ; i < scoring_file_errors.length ; i++){
            if (i < MAX_ERRORS_PER_FILE){
                let validation_error = scoring_file_errors[i];
                table_html += "<tr><td><b>" + validation_error.row + "</b></td><td>";
                table_html += report_items_2_html(validation_error.messages);
                table_html += '</td></tr>';
            } else {
                table_html += "<tr><td colspan=\"2\">Over "+MAX_ERRORS_PER_FILE+" errors found. Showing first "+MAX_ERRORS_PER_FILE+" only.</td></tr>";
                break;
            }
        }
        table_html += '</tbody></table>';
        this.root_node.append(table_html);
    }

}

async function displayResults(response, score_report){
    for (let i = 0; i < response.length; i++){
        let file_report = response[i];
        let valid = file_report.valid;
        if (valid) {
            score_report.set_status_valid();
        } else {
            score_report.set_status_invalid();
            score_report.addReportTable(file_report.errors, 'Error(s)');
        }
    }
}


async function validation(validateFileHandle) {
    let contexts = [];
    if (!validateFileHandle && dirHandle) {
        console.log('Validating multiple files in selected directory');

        for await (const [name, handle] of dirHandle.entries()) {
            if(handle.kind === 'file'){
                contexts.push({
                    dirHandle: dirHandle,
                    outputFileName: name,
                })
            }
        }
    } else if (validateFileHandle && dirHandle) {
        contexts.push({
            dirHandle: dirHandle,
            outputFileName: validateFileHandle.name,
        });
    } else if (webkitFiles) {
        for (const file of webkitFiles) {
            contexts.push({
                webkitfile: file,
                outputFileName: file.name,
            })
        }
    }

    try {
        let validation_output_div = $("#validation_out");
        validation_output_div.html('');
        let reports = [];
        // Adding one or multiple validation reports as placeholders
        for(let i= 0; i < contexts.length; i++) {
            reports.push(new ScoreReport(contexts[i].outputFileName));
        }
        // Starting a worker for each score so results are displayed progressively
        for(let i= 0; i < contexts.length; i++){
            let context = contexts[i];
            let score_report = reports[i];
            score_report.set_status_validating();
            const { results, error } = await asyncRun(validate_scores, context);
            if (results) {
                let data = JSON.parse(results);
                if(data.status === 'success'){
                    await displayResults(data.response, score_report);
                    //console.log("pyodideWorker return results: ", data.response);
                } else if (data.status === 'error'){
                    console.error("pyodideWorker returned error: ", data.error);
                    await appendAlertToElement("error",'Error: '+data.error,'danger')
                }
            } else if (error) {
                console.log("pyodideWorker error: ", error);
                await appendAlertToElement("error",'Error: '+error,'danger')
            }
        }
    } catch (e) {
        await appendAlertToElement("error",`Error in pyodideWorker at ${e.filename}, Line: ${e.lineno}, ${e.message}`,'danger')
        console.error(
            `Error in pyodideWorker at ${e.filename}, Line: ${e.lineno}, ${e.message}`,
        );
    }
}

async function appendAlertToElement(elementId, message, type) {
    const alertPlaceholder = document.getElementById(elementId);
    if (!alertPlaceholder) {
        console.error("Element with ID '" + elementId + "' not found.");
        return;
    }

    const wrapper = document.createElement('div');
    wrapper.innerHTML = [
        `<div class="alert alert-${type} alert-dismissible" role="alert">`,
        `   <div>${message}</div>`,
        '   <div>Please contact the PGS-Catalog support if the problem persists.</div>',
        '   <button type="button" data-bs-dismiss="alert" aria-label="Close"></button>',
        '</div>'
    ].join('');

    alertPlaceholder.append(wrapper);
}

// Adding event listeners to all buttons
document.querySelector('#validate_directory').addEventListener('click', async () => {
    console.log("Initializing validation");
    await validation(null);
});

document.querySelector('#mountvalidate').addEventListener('click', async () => {
    let dirHandle = await mountLocalDirectory();
    let dirName = dirHandle.name;
    successMount(dirName);
    document.querySelector('#validate_single').disabled = false;
    document.querySelector('#validate_directory').disabled = false;
});

document.querySelector('#validate_single').addEventListener('click', async () => {
    [validateFileHandle] = await window.showOpenFilePicker();
    await validation(validateFileHandle);
});

// The following event listeners just forward a click from buttons to hidden input elements,
// that way we can still use our button styles.
document.querySelector('#validate_single_webkit').addEventListener('click', async () => {
    document.getElementById('webkitFilePicker').click();
});

document.querySelector('#validate_directory_webkit').addEventListener('click', async () => {
    document.getElementById('webkitDirPicker').click();
});

function validateWebkitFiles(e){
     for (const file of e.target.files) {
          console.log(file.webkitRelativePath, file);
        }
        webkitFiles = e.target.files;
        validation(null).then(function(){
            console.log("Validation done");
        });
}

// Showing File System Access form if Chromium-based browser, otherwise using webkit files input.
if ('showDirectoryPicker' in window) {
    console.log("Browser compatible with File System Access API.");
    document.getElementById("fsaForm").style.display = "block";
} else {
    console.log("Browser not compatible with File System Access API. Using webkit files instead.");
    document.getElementById("webkitForm").style.display = "block";
    document.getElementById('webkitFilePicker').addEventListener("change", validateWebkitFiles);
    document.getElementById('webkitDirPicker').addEventListener("change", validateWebkitFiles);
}