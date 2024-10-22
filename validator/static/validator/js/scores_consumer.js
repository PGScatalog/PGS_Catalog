import "https://cdn.datatables.net/2.0.3/js/dataTables.js"
import { asyncRun } from "./py-worker.js";


const validate_scores = await fetch(new URL('../python/bin/validation_scores.py', import.meta.url, null)).then(response => response.text());

let dirHandle;
let validateFileHandle;

function startLoading(){
    const spinner = document.getElementById('pgs_loading');
    spinner.style.visibility = "visible";
}

function finishLoading(){
    const spinner = document.getElementById('pgs_loading');
    spinner.style.visibility = "hidden";
}

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
    return dirHandle.name;
}

async function validation(validateFileHandle) {
    let context;
    if (!validateFileHandle) {
        console.log('No single scoring file defined');
        context = {
            dirHandle: dirHandle,
            outputFileName: null,
        };
    } else {
        context = {
            dirHandle: dirHandle,
            outputFileName: validateFileHandle.name,
        };
    }

    try {
        const { results, error } = await asyncRun(validate_scores, context);
        if (results) {
            let data = JSON.parse(results);
            if(data.status === 'success'){
                validation_out.value = data.response;
                console.log("pyodideWorker return results: ", data.response);
            } else if (data.status === 'error'){
                validation_out.value = '';
                console.error("pyodideWorker returned error: ", data.error);
                appendAlertToElement("error",'Error: '+data.error,'danger')
            }
            return results;
        } else if (error) {
            validation_out.value = '';
            console.log(typeof error);
            console.log("pyodideWorker error: ", error);
            appendAlertToElement("error",'Error: '+error,'danger')
        }
    } catch (e) {
        validation_out.value =`Error in pyodideWorker at ${e.filename}, Line: ${e.lineno}, ${e.message}`;
        console.log(
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

document.querySelector('#validate_directory').addEventListener('click', async () => {
    validation_out.value = "Initializing validation...\n";
    //$('#validate').html('<span class="spinner-grow spinner-grow-sm" role="status" aria-hidden="true"></span> Validating...');
    startLoading();
    await validation(null);
    finishLoading();
    //$('#validate').html('<button id="validate" class="btn btn-primary" data-mdb-ripple-init>Validate the selected file</button>');
});

document.querySelector('#mountvalidate').addEventListener('click', async () => {
    if (!('showDirectoryPicker' in window)) {
        alert('Your browser does not support the File System Access API. Please use a supported browser.');
        return; // Stop execution if the API is not supported
    }
    else {
        let dirName = await mountLocalDirectory();
        //appendAlertToElement('validatediv','Nice, you have granted the permission to the local directory '+dirHandle.name,'success' )
        //document.querySelector('#mount').disabled = true;
        successMount(dirName);
        document.querySelector('#validate_single').disabled = false;
        document.querySelector('#validate_directory').disabled = false;
    }
});

document.querySelector('#validate_single').addEventListener('click', async () => {
    [validateFileHandle] = await window.showOpenFilePicker();
    startLoading();
    await validation(validateFileHandle);
    finishLoading();
});
