import http from 'node:http';
import { fileURLToPath } from 'node:url';
import { createStore, HttpError } from './store.js';
import { handleApi, send } from './api.js';
import { serveStatic } from './static.js';
export function createServer(store=createStore()){
  return http.createServer(async(req,res)=>{
    try{
      const url=new URL(req.url,'http://localhost');
      if(await handleApi(store,req,res,url))return;
      if(serveStatic(req,res,url))return;
      send(res,404,{error:'not_found',message:'Not found'});
    }catch(e){
      if(e instanceof HttpError)send(res,e.status,{error:e.code,message:e.message});
      else{console.error(e);send(res,500,{error:'internal_error',message:'Internal error'});}
    }
  });
}
if(process.argv[1]&&fileURLToPath(import.meta.url)===process.argv[1]){
  const port=Number(process.env.PORT||8080);
  createServer().listen(port,'0.0.0.0',()=>console.log('ThermoTrace on port '+port));
}
