// Adapted from https://github.com/EBISPOT/gwas-sumstats-tools-ssf-morph
// This script is setting up a way to run Python scripts asynchronously in a web worker. It sends the Python script to the worker and sets up a callback to handle the result when the worker has finished executing the script.
const pyodideWorker = new Worker(new URL((on_gae) ? "webworker.min.js" : "webworker.js", import.meta.url, null));

const callbacks = {};

pyodideWorker.onmessage = (event) => {
  const { id, ...data } = event.data;
  const onSuccess = callbacks[id];
  delete callbacks[id];
  onSuccess(data);
};
//This id is incremented each time the function is invoked and is kept within the safe integer limit.

let id = 0; // identify a Promise
const asyncRun = async (script, context) => {
  // Runs the given Python script through the Pyodide worker.
  id = (id + 1) % Number.MAX_SAFE_INTEGER;
  return new Promise((onSuccess) => {
    callbacks[id] = onSuccess;
    pyodideWorker.postMessage({
      ...context,
      python: script,
      id,
    });
  });
};

const resetWorker = async () => {
  // Send a reset message to the worker.
  id = (id + 1) % Number.MAX_SAFE_INTEGER;
  return new Promise((onSuccess) => {
    callbacks[id] = onSuccess;
    pyodideWorker.postMessage({
      "reset": true,
      id,
    });
  });
};

export { asyncRun, resetWorker };