<?php

declare(strict_types=1);

final class Router
{
    public function __construct(private AccountService $accounts) {}

    public function dispatch(string $method, string $path, array $query = [], ?array $body = null): array
    {
        if ($method === 'GET' && $path === '/api/accounts') {
            return [200, $this->accounts->list($query['segment'] ?? null)];
        }
        if ($method === 'GET' && preg_match('#^/api/accounts/([^/]+)$#', $path, $m)) {
            return [200, $this->accounts->detail(urldecode($m[1]))];
        }
        if ($method === 'POST' && preg_match('#^/api/accounts/([^/]+)/override$#', $path, $m)) {
            return [200, $this->accounts->setOverride(urldecode($m[1]), $body ?? [])];
        }
        return [404, ['error' => 'not_found']];
    }
}
