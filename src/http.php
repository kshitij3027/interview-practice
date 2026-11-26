<?php
require_once __DIR__.'/domain.php';
require_once __DIR__.'/store.php';
function dispatch(string $method,string $path,string $raw): array {
    try {
        if ($method === 'GET' && $path === '/api/inspections') return [200,withState(false,fn($s)=>directory($s))];
        if (preg_match('~^/api/inspections/([A-Za-z0-9-]+)(/answer)?$~D',$path,$m)) {
            $id=$m[1]; $suffix=$m[2]??'';
            if ($method==='GET' && $suffix==='') return [200,withState(false,fn($s)=>detail($s,$id))];
            if ($method==='POST' && $suffix==='/answer') {
                $body=json_decode($raw,true);
                if (!is_array($body)) throw new ApiError(400,'Expected JSON object');
                return [200,withState(true,fn(&$s)=>saveAnswer($s,$id,$body))];
            }
        }
        throw new ApiError(404,'Route not found');
    } catch (ApiError $e) { return [$e->status,['error'=>$e->getMessage()]+$e->details]; }
}
