<?php

declare(strict_types=1);

final class DataStore
{
    private array $accounts = [];
    private array $signals = [];
    private int $datasetRevision = 1;

    public function __construct(string $fixtureDir)
    {
        $accounts = json_decode((string) file_get_contents($fixtureDir . '/accounts.json'), true, flags: JSON_THROW_ON_ERROR);
        foreach ($accounts as $account) {
            $account['revision'] = 1;
            $account['manual_override'] = null;
            $this->accounts[$account['id']] = $account;
        }

        $lines = file($fixtureDir . '/signals.jsonl', FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) ?: [];
        foreach ($lines as $line) {
            $this->signals[] = json_decode($line, true, flags: JSON_THROW_ON_ERROR);
        }
    }

    public function listAccounts(?string $segment = null): array
    {
        $accounts = array_values($this->accounts);
        if ($segment !== null && $segment !== '') {
            $accounts = array_values(array_filter($accounts, fn(array $a): bool => $a['segment'] === $segment));
        }
        usort($accounts, fn(array $a, array $b): int => strcmp($a['name'], $b['name']));
        return $accounts;
    }

    public function getAccount(string $id): ?array
    {
        return $this->accounts[$id] ?? null;
    }

    public function getSignals(string $accountId): array
    {
        return array_values(array_filter($this->signals, fn(array $s): bool => $s['account_id'] === $accountId));
    }

    public function datasetRevision(): int
    {
        return $this->datasetRevision;
    }

    public function setOverride(string $accountId, ?string $classification, string $reason, int $expectedRevision): array
    {
        if (!isset($this->accounts[$accountId])) {
            throw new DomainException('account_not_found');
        }
        $account = $this->accounts[$accountId];
        if ($account['revision'] !== $expectedRevision) {
            throw new RuntimeException('stale_revision');
        }
        if ($classification !== null && !in_array($classification, ['healthy', 'watch', 'critical'], true)) {
            throw new InvalidArgumentException('invalid_classification');
        }
        if ($classification !== null && trim($reason) === '') {
            throw new InvalidArgumentException('reason_required');
        }

        $account['manual_override'] = $classification === null ? null : [
            'classification' => $classification,
            'reason' => trim($reason),
        ];
        $account['revision']++;
        $this->datasetRevision++;
        $this->accounts[$accountId] = $account;
        return $account;
    }
}
