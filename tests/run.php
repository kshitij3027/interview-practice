<?php

declare(strict_types=1);

require __DIR__ . '/TestHarness.php';
require __DIR__ . '/../src/DataStore.php';
require __DIR__ . '/../src/AccountService.php';
require __DIR__ . '/../src/Router.php';

$t = new TestHarness();
$store = new DataStore(__DIR__ . '/../fixtures');
$service = new AccountService($store);
$router = new Router($service);

$list = $service->list(null);
$t->same(5, count($list['accounts']), 'loads all accounts');
$t->same(['Northstar Labs','Pine Systems','Quartz Health','River Retail','Summit Works'], array_column($list['accounts'], 'name'), 'accounts sorted by name');
$t->same(2, count($service->list('enterprise')['accounts']), 'segment filter');
$detail = $service->detail('acct-102');
$t->same(4, count($detail['signals']), 'raw duplicate observations remain visible');

$updated = $service->setOverride('acct-101', ['classification'=>'watch','reason'=>'Executive sponsor changed','expected_revision'=>1]);
$t->same(2, $updated['account']['revision'], 'override increments account revision once');
$t->same(2, $updated['dataset_revision'], 'override increments dataset revision once');
$t->same('watch', $updated['account']['manual_override']['classification'], 'override stored');

$stale = false;
try { $service->setOverride('acct-101', ['classification'=>'critical','reason'=>'stale','expected_revision'=>1]); } catch (RuntimeException $e) { $stale = $e->getMessage() === 'stale_revision'; }
$t->ok($stale, 'stale override rejected');

$reasonRequired = false;
try { $service->setOverride('acct-102', ['classification'=>'healthy','reason'=>'  ','expected_revision'=>1]); } catch (InvalidArgumentException $e) { $reasonRequired = $e->getMessage() === 'reason_required'; }
$t->ok($reasonRequired, 'override reason required');

[$status, $payload] = $router->dispatch('GET','/api/accounts',['segment'=>'smb']);
$t->same(200, $status, 'router returns list');
$t->same('acct-104', $payload['accounts'][0]['id'], 'router passes segment filter');

$cleared = $service->setOverride('acct-101', ['classification'=>null,'reason'=>'','expected_revision'=>2]);
$t->same(null, $cleared['account']['manual_override'], 'override can be cleared');
$t->same(3, $cleared['account']['revision'], 'clear increments revision once');

$t->finish();
