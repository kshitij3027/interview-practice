<?php

declare(strict_types=1);

final class TestHarness
{
    private int $passed = 0;
    private int $failed = 0;
    public function ok(bool $condition, string $name): void { if ($condition) { $this->passed++; echo "PASS $name\n"; } else { $this->failed++; echo "FAIL $name\n"; } }
    public function same(mixed $expected, mixed $actual, string $name): void { $this->ok($expected === $actual, $name . ($expected === $actual ? '' : ' expected=' . json_encode($expected) . ' actual=' . json_encode($actual))); }
    public function finish(): never { echo "\n{$this->passed} passed, {$this->failed} failed\n"; exit($this->failed === 0 ? 0 : 1); }
}
