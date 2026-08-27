<?php

declare(strict_types=1);

require __DIR__ . '/src/DataStore.php';
require __DIR__ . '/src/AccountService.php';
require __DIR__ . '/src/Http.php';
require __DIR__ . '/src/Router.php';

if (PHP_SAPI === 'cli-server') {
    $path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
    $public = __DIR__ . '/public' . $path;
    if ($path !== '/' && is_file($public)) return false;
}

static $router = null;
if ($router === null) {
    $store = new DataStore(__DIR__ . '/fixtures');
    $router = new Router(new AccountService($store));
}

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
if ($method === 'OPTIONS') Http::json([], 204);
if ($path === '/' || $path === '/index.html') {
    header('Content-Type: text/html');
    readfile(__DIR__ . '/public/index.html');
    exit;
}

try {
    [$status, $payload] = $router->dispatch($method, $path, $_GET, $method === 'POST' ? Http::body() : null);
    Http::json($payload, $status);
} catch (InvalidArgumentException $e) {
    Http::json(['error' => $e->getMessage()], 400);
} catch (RuntimeException $e) {
    Http::json(['error' => $e->getMessage()], $e->getMessage() === 'stale_revision' ? 409 : 400);
} catch (DomainException $e) {
    Http::json(['error' => $e->getMessage()], 404);
}
