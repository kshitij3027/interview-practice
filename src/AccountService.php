<?php

declare(strict_types=1);

final class AccountService
{
    public function __construct(private DataStore $store) {}

    public function list(?string $segment): array
    {
        return [
            'accounts' => $this->store->listAccounts($segment),
            'dataset_revision' => $this->store->datasetRevision(),
        ];
    }

    public function detail(string $id): array
    {
        $account = $this->store->getAccount($id);
        if ($account === null) {
            throw new DomainException('account_not_found');
        }
        return [
            'account' => $account,
            'signals' => $this->store->getSignals($id),
            'dataset_revision' => $this->store->datasetRevision(),
        ];
    }

    public function setOverride(string $id, array $body): array
    {
        $classification = $body['classification'] ?? null;
        $reason = (string) ($body['reason'] ?? '');
        $expectedRevision = $body['expected_revision'] ?? null;
        if (!is_int($expectedRevision)) {
            throw new InvalidArgumentException('expected_revision_required');
        }
        $account = $this->store->setOverride($id, $classification, $reason, $expectedRevision);
        return ['account' => $account, 'dataset_revision' => $this->store->datasetRevision()];
    }
}
