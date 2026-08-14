import http from 'node:http';
import { DataStore } from './src/dataStore.js';
import { ExperimentService } from './src/experimentService.js';
import { createHandler } from './src/routes.js';

const store = new DataStore();
const service = new ExperimentService(store);
const server = http.createServer(createHandler(service));
const port = Number(process.env.PORT ?? 3001);
server.listen(port, () => console.log(`Signal Lab API listening on http://localhost:${port}`));
