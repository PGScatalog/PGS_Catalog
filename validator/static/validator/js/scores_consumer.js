const pyworker = await import((on_gae)?'./py-worker.min.js':'./py-worker.js');
const asyncRun = pyworker.asyncRun;

const validate_scores = await fetch(new URL('../python/bin/validation_scores.py', import.meta.url, null)).then(response => response.text());

let dirHandle;
let validateFileHandle;

function toggleLoading(on){
    const spinner = document.getElementById('pgs_loading');
    spinner.style.visibility = on ? "visible" : "hidden";
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
    toggleLoading(true);
    await validation(null);
    toggleLoading(false);
});

document.querySelector('#mountvalidate').addEventListener('click', async () => {
    if (!('showDirectoryPicker' in window)) {
        alert('Your browser does not support the File System Access API. Please use a supported browser.');
        return; // Stop execution if the API is not supported
    }
    else {
        let dirName = await mountLocalDirectory();
        successMount(dirName);
        document.querySelector('#validate_single').disabled = false;
        document.querySelector('#validate_directory').disabled = false;
    }
});

document.querySelector('#validate_single').addEventListener('click', async () => {
    [validateFileHandle] = await window.showOpenFilePicker();
    toggleLoading(true);
    await validation(validateFileHandle);
    toggleLoading(false);
});
