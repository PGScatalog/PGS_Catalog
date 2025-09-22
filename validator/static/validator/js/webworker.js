// webworker.js
// Adapted from https://github.com/EBISPOT/gwas-sumstats-tools-ssf-morph

// Setup your project to serve `py-worker.js`. You should also serve
// `pyodide.js`, and all its associated `.asm.js`, `.json`,
// and `.wasm` files as well:
importScripts("https://cdn.jsdelivr.net/pyodide/v0.28.2/full/pyodide.js");
// pgscatalog.core 1.0.1 and pyodide 0.28.2 both work with pyodide 2.10.6

const wheels_base_url = "/static/validator/python/wheels/";

async function loadPyodideAndPackages() {
    self.pyodide = await loadPyodide();
    // Loading pyodide distributed packages. Those include compiled binary files and can't be installed with pip.
    // pydantic is installed here to ensure the version works with distributed pydantic-core
    // lzma is required by xopen from pgscatalog.core
    await pyodide.loadPackage(["micropip","pydantic","pydantic-core","lzma"]);

    const micropip = pyodide.pyimport("micropip");
    await micropip.install(['openpyxl','requests','pgscatalog.core==1.0.1']);
    await micropip.install(wheels_base_url+"pgs_template_validator-1.1.3-py3-none-any.whl", keep_going=true);
    await micropip.install(wheels_base_url+"pgscatalog_validate-0.2-py3-none-any.whl", keep_going=true)
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
        if(context["reset"]){ // Reset needed if changing File System Access directory
            console.log("Resetting worker");
            self.pyodide.FS.unmount("/data");
            self.pyodide.FS.rmdir("/data");
            self.fsmounted = false;
            self.nativefs = null;
            self.postMessage({ "reset": true, id });
        } else {
            await self.pyodide.loadPackagesFromImports(python);
            // mount local directory, make the nativefs as a global vaiable.
            if (!self.fsmounted && self.dirHandle) {
                self.nativefs = await self.pyodide.mountNativeFS("/data", self.dirHandle);
                self.fsmounted = true;
            } else if (self.webkitfile) {
                // Copy the file into pyodide virtual FS
                if (!self.fsmounted) {
                    self.pyodide.FS.mkdir("/data");
                    self.fsmounted = true
                }
                // Copy file into Pyodide FS so Python can access it
                const buffer = await self.webkitfile.arrayBuffer();
                self.pyodide.FS.writeFile("/data/" + self.webkitfile.name, new Uint8Array(buffer));
            }
            // Run python script
            self.pyodide.globals.set('print', s => console.log(s))
            let results = await self.pyodide.runPythonAsync(python);
            // Flush new files to disk
            if (self.nativefs) {
                await self.nativefs.syncfs();
            }
            // Cleaning virtual file. Don't do this if using mounted native FS!
            if (self.webkitfile) {
                self.pyodide.FS.unlink("/data/" + self.webkitfile.name);
            }

            self.postMessage({results, id});
        }
    } catch (error) {
        console.log(error);
        self.postMessage({error: error.message, id});
    }
  };
