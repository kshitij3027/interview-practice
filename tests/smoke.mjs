import {spawn} from 'node:child_process';
import {mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import assert from 'node:assert/strict';
const dir=await mkdtemp(join(tmpdir(),'fieldkit-'));const port=18000+Math.floor(Math.random()*20000);const base=`http://127.0.0.1:${port}`;
const p=spawn('php',['-S',`127.0.0.1:${port}`,'-t','public','public/router.php'],{env:{...process.env,FIELDKIT_STATE:join(dir,'state.json')},stdio:'ignore'});
try{let ready=false;for(let i=0;i<50;i++){try{if((await fetch(base)).ok){ready=true;break;}}catch{}await new Promise(r=>setTimeout(r,100));}assert.ok(ready);assert.match(await (await fetch(base)).text(),/FieldKit/);assert.equal((await fetch(base+'/app.js')).status,200);
const url=base+'/api/inspections/I-101';let r=await fetch(url);assert.equal((await r.json()).revision,4);const post=()=>fetch(url+'/answer',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({fieldId:'capacity',value:0,expectedRevision:4})});r=await post();assert.equal(r.status,200);assert.equal((await r.json()).revision,5);assert.equal((await post()).status,409);assert.equal((await (await fetch(url)).json()).answers.capacity,0);assert.equal((await fetch(base+'/api/inspections/missing')).status,404);console.log('PASS live HTTP and persistent answer smoke');}finally{p.kill();await new Promise(r=>p.once('exit',r));await rm(dir,{recursive:true,force:true});}
