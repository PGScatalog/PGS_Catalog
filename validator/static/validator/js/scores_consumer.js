const pyworker = await import((on_gae)?'./py-worker.min.js':'./py-worker.js');
const asyncRun = pyworker.asyncRun;

const validate_scores = await fetch(new URL('../python/bin/validation_scores.py', import.meta.url, null)).then(response => response.text());

let dirHandle;
let validateFileHandle;

const MAX_ERRORS_PER_FILE = 50;
const ALLOWED_FILE_EXTENSIONS = ['.txt','.txt.gz','.tsv','.tsv.gz','.csv','.csv.gz','.xlsx'];

function successMount(dirName){
    document.getElementById('grant_message').innerHTML = 'Authorization granted on directory \"'+dirName+"\".";
}

async function mountLocalDirectory() {
    // use the same ID crypt4gh to open pickers in the same directory
    let newDirHandle = await showDirectoryPicker();

    if ((await newDirHandle.queryPermission({ mode: "read" })) !== "granted") {
        if (
            (await dirHandle.requestPermission({ mode: "read" })) !== "granted"
        ) {
            throw Error("Unable to read and write directory");
        }
    }
    return newDirHandle;
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
    constructor(score_name, id) {
        let validation_output_div = $("#validation_out");
        this.id = id;
        this.status_icon = $("<i title=\"Queuing\" class=\"fa fa-clock\"></i>"); // Queuing status
        this.root_node = $("<div class=\"mt-4\"></div>");
        this.title = $("<h5>"+score_name+" </h5>");
        this.title.append(this.status_icon);
        this.root_node.append(this.title.wrap("<div></div>").parent());
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

    set_status_error(){
        this.status_icon.removeClass();
        this.status_icon.addClass("fa fa-triangle-exclamation pgs_color_amber");
        this.status_icon.prop("title", "Error");
    }

    addReportTable(scoring_file_errors, items_header) {
        let table_html = '<div class="ml-5" id="result_'+this.id+'"><table class="table table-bordered" style="width:auto"><thead class="thead-light">' +
            '<tr><th>Row</th><th>' + items_header + '</th></tr>' +
            '</thead><tbody>';
        // Looping through the errors up the maximum allowed
        for(let i = 0 ; i < scoring_file_errors.length ; i++){
            if (i < MAX_ERRORS_PER_FILE){
                let validation_error = scoring_file_errors[i];
                table_html += "<tr><td><b>" + validation_error.row + "</b></td><td>"
                 + report_items_2_html(validation_error.messages) + '</td></tr>';
            } else {
                table_html += "<tr><td colspan=\"2\">Over "+MAX_ERRORS_PER_FILE+" errors found. Showing first "+MAX_ERRORS_PER_FILE+" only.</td></tr>";
                break;
            }
        }
        table_html += '</tbody></table></div>';
        this.table = $(table_html);
        this.root_node.append(this.table);

        // Expand/Collapse
        this.title.append("<i class=\"fa fa-chevron-right ml-2 expand-collapse-rotate\"></i>\n");
        this.title.wrap("<span role=\"button\" data-toggle=\"collapse\" data-target=\"#result_"+this.id+"\" " +
            "aria-expanded=\"true\" aria-controls=\"result_"+this.id+"\"></span>")
        this.table.addClass("collapse show");
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

function filename_is_valid(filename){
    // Only considering files with proper extension
    return ALLOWED_FILE_EXTENSIONS.some(ext => filename.endsWith(ext))
        // And not hidden
        && !filename.startsWith('.');
}


async function validation(validateFileHandle, webkitFiles) {
    let contexts = [];
    if (!validateFileHandle && dirHandle) {
        console.log('Validating multiple files in selected directory');

        for await (const [name, handle] of dirHandle.entries()) {
            if(handle.kind === 'file' && filename_is_valid(name)){
                contexts.push({
                    dirHandle: dirHandle,
                    outputFileName: name,
                })
            } else {
                console.log("Ignored file '"+name+"'");
            }
        }
    } else if (validateFileHandle && dirHandle) {
        contexts.push({
            dirHandle: dirHandle,
            outputFileName: validateFileHandle.name,
        });
    } else if (webkitFiles) {
        for (const file of webkitFiles) {
            if(filename_is_valid(file.name)){
                contexts.push({
                    webkitfile: file,
                    outputFileName: file.name,
                })
            } else {
                console.log("Ignored file '"+file.name+"'");
            }
        }
    }

    try {
        let validation_output_div = $("#validation_out");
        validation_output_div.html('');
        let reports = [];
        // Adding one or multiple validation reports as placeholders
        for(let i= 0; i < contexts.length; i++) {
            reports.push(new ScoreReport(contexts[i].outputFileName, i));
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
                    score_report.set_status_error();
                    await appendAlertToElement("error",'Error: '+data.error,'danger')
                }
            } else if (error) {
                console.log("pyodideWorker error: ", error);
                score_report.set_status_error();
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
        '   <button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
        '    <span aria-hidden="true">&times;</span>' +
        '  </button>',
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
    mountLocalDirectory().then(async(newDirHandle) => {
        // If a directory was previously selected, reset the worker to unmount that directory
        if (dirHandle){
            await pyworker.resetWorker();
        }
        dirHandle = newDirHandle;
        let dirName = newDirHandle.name;
        successMount(dirName);
        document.getElementById('fsaForm_2').style.display = "block";
        document.getElementById('validate_single').disabled = false;
        document.getElementById('validate_directory').disabled = false;
    }).catch(err => {
        if (err.name === 'AbortError') {
          console.log("User canceled directory selection.");
        } else {
          console.error("Something went wrong:", err);
        }
  });
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

function  validateWebkitSingleFile(e){
    const file = e.target.files[0];
    validation(null, [file]).then(function(){
        console.log("Validation done");
     });
}

function validateWebkitMultipleFiles(e){
    let webkitFiles = [];
     for (const file of e.target.files) {
         // Only selecting files in toplevel selected directory
         if(file.webkitRelativePath.split("/").length === 2){
             console.log(file.webkitRelativePath, file);
             webkitFiles.push(file);
         }
     }
     validation(null, webkitFiles).then(function(){
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
    document.getElementById('webkitFilePicker').addEventListener("change", validateWebkitSingleFile);
    document.getElementById('webkitDirPicker').addEventListener("change", validateWebkitMultipleFiles);
}

// Injecting the list of allowed file extensions in the page.
$('.allowed_extensions').html(ALLOWED_FILE_EXTENSIONS.join(", "));