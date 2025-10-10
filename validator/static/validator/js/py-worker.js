// Adapted from https://github.com/EBISPOT/gwas-sumstats-tools-ssf-morph
// This script is setting up a way to run Python scripts asynchronously in a web worker. It sends the Python script to the worker and sets up a callback to handle the result when the worker has finished executing the script.
const pyodideWorker = new Worker(new URL((on_gae) ? "webworker.min.js" : "webworker.js", import.meta.url, null));

const callbacks = {};

/**
 * Handles messages received from the Pyodide worker.
 *
 * Matches each incoming message by its `id` to a stored callback
 * (created by {@link postMessage}) and resolves the corresponding promise.
 * Cleans up the callback entry afterward to prevent memory leaks.
 *
 * @param {MessageEvent} event - Message event from the worker.
 */
pyodideWorker.onmessage = (event) => {
  const { id, ...data } = event.data;
  const onSuccess = callbacks[id];
  if (onSuccess) {
    delete callbacks[id];
    onSuccess(data);
  }
};
//This id is incremented each time the function is invoked and is kept within the safe integer limit.

let id = 0; // identify a Promise
let initPromise = null; // Store the init promise to ensure it's complete before subsequent script runs

/**
 * Sends a message to the Pyodide web worker and returns a promise that resolves
 * when a response with the corresponding message ID is received.
 *
 * This function acts as a wrapper around the standard `postMessage` API, providing
 * request–response correlation by assigning a unique numeric ID to each outgoing
 * message. When the worker posts a reply with the same `id`, the stored callback
 * is invoked to resolve the original promise.
 *
 * @function postMessage
 * @param {Object} message - The data payload to send to the worker.
 *
 * @returns {Promise<Object>} A promise that resolves with the worker’s response message,
 * once it posts a reply containing the matching `id`.
 */
const postMessage = (message) => {
  id = (id + 1) % Number.MAX_SAFE_INTEGER;
  return new Promise((resolve) => {
    callbacks[id] = resolve;
    pyodideWorker.postMessage({ id, ...message });
  });
};

/**
 * Initializes the worker environment by installing the given dependencies.
 *
 * This function must be called **before** any other "run" or execution functions,
 * as it ensures that all required packages and static files are loaded inside the worker.
 *
 * @async
 * @function initWorker
 * @param {Object} dependencies - A configuration object defining which resources to install.
 * @param {string[]} [dependencies.pyodide_packages] - A list of packages to be loaded via Pyodide's built-in package manager.
 * @param {string[]} [dependencies.pip_packages] - A list of Python packages (or wheel URLs) to install using `micropip`.
 * @param {Object[]} [dependencies.static_files] - A list of objects describing static files to preload into the Pyodide file system.
 * @param {string} dependencies.static_files[].name - The target filename inside the worker’s virtual file system.
 * @param {string} dependencies.static_files[].url - The source URL of the file to be loaded.
 *
 * @returns {Promise<Object>} A promise that resolves once the worker and all dependencies
 * have been successfully initialized. The same promise is returned on repeated calls.
 *
 * @example
 * const dependencies = {
 *   pyodide_packages: ["micropip", "pydantic", "pydantic-core", "lzma"],
 *   pip_packages: [
 *     "openpyxl",
 *     "pgscatalog.core==1.0.1",
 *     "/static/validator/python/wheels/pgscatalog_validate-0.2-py3-none-any.whl",
 *   ],
 *   static_files: [],
 * };
 *
 * // Initialize the worker before running any code
 * await initWorker(dependencies);
 */
const initWorker = async (dependencies) => {
  if (!initPromise) {
    // Store the promise so other functions can await it
    initPromise = postMessage({
      type: "init",
      dependencies,
    }).then((res) => {
      if (res.error) throw new Error(res.error);
      return res;
    });
  }
  return initPromise; // subsequent calls reuse same promise
};

/**
 * Executes a Python script inside the initialized worker environment.
 *
 * This function sends a message to the worker containing the Python code
 * to be executed, along with an optional execution context.
 * It waits for the worker initialization (`initWorker`) to complete
 * before sending the message, ensuring that all dependencies are available.
 *
 * @async
 * @function asyncRun
 * @param {string} script - The Python code to execute inside the worker.
 * @param {Object} [context] - Optional execution context to include in the message.
 *
 * @returns {Promise<Object>} A promise that resolves with the worker’s response,
 * typically containing the script output or execution result.
 *
 * @example
 * await initWorker(dependencies);
 * const result = await asyncRun("print('Hello from Pyodide!')");
 * console.log(result);
 */
const asyncRun = async (script, context) => {
  await initPromise; // wait until initWorker is done
  return postMessage({
    ...context,
    python: script,
  });
};

/**
 * Resets the worker file system to its initial state.
 *
 * This function requests the worker to clear its working virtual filesystem in order to run a script
 * on a new mounted directory.
 *
 * It waits for the worker initialization (`initWorker`) to complete before
 * issuing the reset command, ensuring the worker is in a valid state.
 *
 * @async
 * @function resetWorker
 * @returns {Promise<Object>} A promise that resolves once the worker acknowledges
 * the reset operation.
 *
 * @example
 * await initWorker(dependencies);
 * await asyncRun(python_script, {dirHandle: dir1, ...});
 * await resetWorker(); // clears the worker’s Python environment
 * await asyncRun(python_script, {dirHandle: dir2, ...});
 */
const resetWorker = async () => {
  await initPromise; // wait until initWorker is done
  return postMessage({ reset: true });
};

export { asyncRun, resetWorker, initWorker };