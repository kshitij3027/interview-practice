import { loadFixtures } from '../src/fixtures.js';
const data = loadFixtures();
console.log('validated ' + data.suites.length + ' suites / ' + data.runs.length + ' runs / ' + data.cases.length + ' cases / ' + data.observations.length + ' observations');
