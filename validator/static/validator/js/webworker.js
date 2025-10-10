// webworker.js
// Adapted from https://github.com/EBISPOT/gwas-sumstats-tools-ssf-morph

// Set up your project to serve `py-worker.js`. You should also serve
// `pyodide.js`, and all its associated `.asm.js`, `.json`,
// and `.wasm` files as well:
importScripts("https://cdn.jsdelivr.net/pyodide/v0.28.2/full/pyodide.js");

async function init(dependencies){
    const pyodide_packages = dependencies['pyodide_packages'];
    const pip_packages = dependencies['pip_packages'];
    const static_files = dependencies['static_files']
    self.pyodide = await loadPyodide();

    if(pyodide_packages){
        await pyodide.loadPackage(pyodide_packages);
    }
    if(pip_packages){
        const micropip = pyodide.pyimport("micropip");
        await micropip.install(pip_packages);
    }
    if(static_files){
        for (const static_file of static_files){
            await pyodide.FS.createLazyFile('/home/pyodide/', static_file['name'],
            static_file['url'], true, false);
        }
    }
    self.is_initialized = true;
    console.log("Worker initialized.");
}


//This event is fired when the worker receives a message from the main thread via the postMessage method.
self.onmessage = async (event) => {
    const { id, type, python, ...context } = event.data;

    if(type === "init"){
        await init(context['dependencies']);
        self.postMessage({status: 'success', id});
        return;
    }
    // Make sure loading is done
    if(!self.is_initialized){
        self.postMessage({error: 'Worker is not initialized', id})
    }

    // Copying the context into the worker
    for (const key of Object.keys(context)) {
      self[key] = context[key];
    }

    try {
        if(type === "reset"){ // Reset needed if changing File System Access directory
            console.log("Resetting worker");
            self.pyodide.FS.unmount("/data");
            self.pyodide.FS.rmdir("/data");
            self.fsmounted = false;
            self.nativefs = null;
            self.postMessage({ "reset": true, id });
        } else { // Preparing files and filesystem before running the Python script.
            // Mount local directory, make the nativefs as a global variable.
            if (!self.fsmounted && self.dirHandle) {
                self.nativefs = await self.pyodide.mountNativeFS("/data", self.dirHandle);
                self.fsmounted = true;
            } else if (self.webkitfile) {
                // Copy the file into pyodide virtual FS
                if (!self.fsmounted) {
                    self.pyodide.FS.mkdir("/data");
                    self.fsmounted = true;
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
            // Cleaning virtual file. Don't do this if using mounted native FS! (Read-only access should already protect against this)
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
