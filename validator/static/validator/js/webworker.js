// webworker.js
// Adapted from https://github.com/EBISPOT/gwas-sumstats-tools-ssf-morph

// Setup your project to serve `py-worker.js`. You should also serve
// `pyodide.js`, and all its associated `.asm.js`, `.json`,
// and `.wasm` files as well:
importScripts("https://cdn.jsdelivr.net/pyodide/v0.26.0/full/pyodide.js");

const wheels_base_url = "/static/validator/python/wheels/";

async function loadPyodideAndPackages() {
    self.pyodide = await loadPyodide();
    await pyodide.loadPackage("micropip");
    const micropip = pyodide.pyimport("micropip");
    await micropip.install(['openpyxl','requests','httpx==0.26.0','tenacity','pyliftover',
        'xopen==1.8.0','zstandard','tqdm','natsort','pandas','pandas-schema']);
    await micropip.install(wheels_base_url+"pgs_template_validator-1.1.3-py3-none-any.whl", keep_going=true);
    await micropip.install(wheels_base_url+"pgscatalog_validate-0.1-py3-none-any.whl", keep_going=true)
    await pyodide.FS.createLazyFile('/home/pyodide/', 'TemplateColumns2Models.xlsx',
            '/static/validator/template/TemplateColumns2Models.xlsx', true, false);
}
let pyodideReadyPromise = loadPyodideAndPackages();


//This event is fired when the worker receives a message from the main thread via the postMessage method.
self.onmessage = async (event) => {
    // make sure loading is done
    await pyodideReadyPromise;
    // Don't bother yet with this line, suppose our API is built in such a way:
    const { id, python, ...context } = event.data;
    // The worker copies the context in its own "memory" (an object mapping name to values)
    for (const key of Object.keys(context)) {
      self[key] = context[key];
    }
    // Now is the easy part, the one that is similar to working in the main thread:
    try {
      await self.pyodide.loadPackagesFromImports(python);
      // mount local directory, make the nativefs as a global vaiable.
      if (! self.fsmounted && self.dirHandle){
        self.nativefs = await self.pyodide.mountNativeFS("/data", self.dirHandle);
        self.fsmounted = true;
      }
      // run python script
      self.pyodide.globals.set('print', s => console.log(s))
      let results = await self.pyodide.runPythonAsync(python);
      // flush new files to disk
        if(self.nativefs){
            await self.nativefs.syncfs();
        }

      self.postMessage({ results, id });
    } catch (error) {
        console.log(error);
      self.postMessage({ error: error.message, id });
    }
  };
