import { writable } from 'svelte/store';

function getItemFromLocalStorage(key, defaultValue) {
  const storedValue = localStorage.getItem(key);
  if (storedValue) {
      return storedValue;
  }
  localStorage.setItem(key, defaultValue);
  return defaultValue;
}

function subscribeAndStore(store, key, defaultValue) {
  store.set(getItemFromLocalStorage(key, defaultValue));
  store.subscribe(value => {
      localStorage.setItem(key, value);
  });
}

export const messages = writable([]);
export const projectFiles = writable(null);

export const selectedProject = writable('');
export const selectedModel = writable('');
export const selectedSearchEngine = writable('');

subscribeAndStore(selectedProject, 'selectedProject', 'select project');
subscribeAndStore(selectedModel, 'selectedModel', 'select model');
subscribeAndStore(selectedSearchEngine, 'selectedSearchEngine', 'select search engine');

export const projectList = writable([]);
export const modelList = writable({});
export const searchEngineList = writable([]);

export const serverStatus = writable(false);
export const internet = writable(true);

export const agentState = writable(null);
export const isSending = writable(false);

export const tokenUsage = writable(0);