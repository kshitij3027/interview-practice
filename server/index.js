import {makeCatalog} from './catalog.js';
import {createServer} from './http.js';
const port=Number(process.env.PORT||8080);
createServer(makeCatalog()).listen(port,'127.0.0.1',()=>console.log(`OfferStream listening on http://127.0.0.1:${port}`));
