import fs from 'node:fs';
const accounts=JSON.parse(fs.readFileSync(new URL('../fixtures/accounts.json',import.meta.url),'utf8'));
const initialFlag={key:'smart-compose',name:'Smart Compose',description:'AI-assisted response drafting',enabled:false,revision:1,overrides:{'acct-102':true}};
export function createStore(){const state={accounts:structuredClone(accounts),flag:structuredClone(initialFlag),datasetRevision:1};return{
 listAccounts(){return structuredClone(state.accounts)}, getFlag(){return structuredClone(state.flag)}, snapshot(){return structuredClone(state)},
 setOverride(accountId,enabled,expectedRevision){if(!state.accounts.some(a=>a.id===accountId))return{error:'account_not_found'};if(expectedRevision!==state.flag.revision)return{error:'stale',currentRevision:state.flag.revision};state.flag.overrides[accountId]=enabled;state.flag.revision++;state.datasetRevision++;return{flag:structuredClone(state.flag),datasetRevision:state.datasetRevision}}
}}