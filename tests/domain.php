<?php
require_once __DIR__.'/../src/domain.php';
$s=json_decode(file_get_contents(__DIR__.'/../fixtures/workspace.json'),true,512,JSON_THROW_ON_ERROR);
function check($ok,$name){if(!$ok)throw new Exception($name);echo "PASS $name\n";}
function status(callable $f){try{$f();return 200;}catch(ApiError $e){return $e->status;}}
check(count(directory($s))===5,'directory');
check(detail($s,'I-101')['version']===1 && detail($s,'I-101')['latestVersion']===3,'pinned schema');
check(saveAnswer($s,'I-101',['fieldId'=>'isolation','value'=>false,'expectedRevision'=>4])['revision']===4,'false no-op');
check(saveAnswer($s,'I-101',['fieldId'=>'capacity','value'=>0,'expectedRevision'=>4])['revision']===5,'zero save');
check(status(fn()=>saveAnswer($s,'I-101',['fieldId'=>'capacity','value'=>'0','expectedRevision'=>5]))===400,'strict type');
check(status(fn()=>saveAnswer($s,'I-101',['fieldId'=>'capacity','value'=>1,'expectedRevision'=>4]))===409,'stale');
check(status(fn()=>saveAnswer($s,'I-103',['fieldId'=>'capacity','value'=>1,'expectedRevision'=>5]))===409,'completed');
check(saveAnswer($s,'I-101',['fieldId'=>'capacity','value'=>null,'expectedRevision'=>5])['revision']===6 && !array_key_exists('capacity',$s['inspections'][0]['answers']),'clear');
