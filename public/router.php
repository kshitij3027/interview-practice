<?php
$path=parse_url($_SERVER['REQUEST_URI'],PHP_URL_PATH);
if ($path==='/' || in_array($path,['/app.js','/api.js','/style.css'],true)) return false;
require_once dirname(__DIR__).'/src/http.php';
try { [$status,$body]=dispatch($_SERVER['REQUEST_METHOD'],$path,file_get_contents('php://input')); }
catch (Throwable $e) { error_log((string)$e); $status=500; $body=['error'=>'Server error']; }
http_response_code($status); header('Content-Type: application/json'); header('Cache-Control: no-store'); echo json_encode($body,JSON_THROW_ON_ERROR);
