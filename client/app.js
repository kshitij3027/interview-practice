import { setupList } from './list.js';
import { setupDetail } from './detail.js';
const list=setupList(id=>detail.select(id));
const detail=setupDetail(()=>list.load());
list.load();
