<?php
class ApiError extends RuntimeException {
    public function __construct(public int $status, string $message, public array $details = []) { parent::__construct($message); }
}
function inspectionIndex(array $state, string $id): int {
    foreach ($state['inspections'] as $i => $record) if ($record['id'] === $id) return $i;
    throw new ApiError(404, 'Inspection not found');
}
function templateFor(array $state, string $id): array {
    foreach ($state['templates'] as $t) if ($t['id'] === $id) return $t;
    throw new LogicException('Unknown template');
}
function fieldsFor(array $template, int $version): array {
    foreach ($template['versions'] as $v) if ($v['version'] === $version) return $v['fields'];
    throw new LogicException('Unknown version');
}
function validAnswer(array $f, mixed $value): bool {
    return match($f['type']) {
        'boolean' => is_bool($value),
        'text' => is_string($value) && strlen($value) <= 500,
        'integer' => is_int($value) && $value >= ($f['min'] ?? PHP_INT_MIN) && $value <= ($f['max'] ?? PHP_INT_MAX),
        'choice' => is_string($value) && in_array($value, $f['choices'], true),
        default => false
    };
}
function detail(array $state, string $id): array {
    $r = $state['inspections'][inspectionIndex($state, $id)];
    $t = templateFor($state, $r['templateId']);
    return $r + ['fields'=>fieldsFor($t, $r['version']), 'templateName'=>$t['name'], 'latestVersion'=>max(array_column($t['versions'], 'version'))];
}
function directory(array $state): array {
    $rows = array_map(fn($r)=>array_intersect_key($r, array_flip(['id','asset','templateId','version','revision','status'])), $state['inspections']);
    usort($rows, fn($a,$b)=>strcmp($a['id'],$b['id']));
    return $rows;
}
function saveAnswer(array &$state, string $id, array $body): array {
    $i = inspectionIndex($state, $id);
    $r = &$state['inspections'][$i];
    if (!is_int($body['expectedRevision'] ?? null) || !is_string($body['fieldId'] ?? null) || !array_key_exists('value',$body)) throw new ApiError(400,'Invalid answer request');
    if ($r['status'] !== 'draft' || $body['expectedRevision'] !== $r['revision']) throw new ApiError(409,'Draft changed or closed',['currentRevision'=>$r['revision'],'currentVersion'=>$r['version']]);
    $fields = array_column(fieldsFor(templateFor($state,$r['templateId']),$r['version']),null,'id');
    $key = $body['fieldId']; $value = $body['value'];
    if (!isset($fields[$key]) || ($value !== null && !validAnswer($fields[$key],$value))) throw new ApiError(400,'Invalid field or value');
    if (($r['answers'][$key] ?? null) !== $value) {
        if ($value === null) unset($r['answers'][$key]); else $r['answers'][$key] = $value;
        $r['revision']++;
    }
    return detail($state,$id);
}
