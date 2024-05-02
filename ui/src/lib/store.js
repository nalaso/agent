import { writable } from 'svelte/store';

export const messages = writable([]);

export const storeSelectedProject = writable('');
export const selectedModel = writable('');

export const projectList = writable([]);
export const modelList = writable({});
export const searchEngineList = writable([]);

export const serverStatus = writable(false);
export const agentState = writable(null);
export const isSending = writable(false);

export const internet = writable(true);
export const tokenUsage = writable(0);