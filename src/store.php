<?php
function withState(bool $write, callable $action): mixed {
    $path = getenv('FIELDKIT_STATE') ?: dirname(__DIR__).'/data/state.json';
    if (!is_dir(dirname($path))) mkdir(dirname($path), 0777, true);
    $lock = fopen($path.'.lock','c');
    if (!$lock || !flock($lock, LOCK_EX)) throw new RuntimeException('State unavailable');
    try {
        $state = json_decode(file_get_contents(is_file($path) ? $path : dirname(__DIR__).'/fixtures/workspace.json'),true,512,JSON_THROW_ON_ERROR);
        $result = $action($state);
        if ($write) {
            $tmp = $path.'.tmp';
            if (file_put_contents($tmp,json_encode($state,JSON_THROW_ON_ERROR)) === false || !rename($tmp,$path)) throw new RuntimeException('State write failed');
        }
        return $result;
    } finally { flock($lock, LOCK_UN); fclose($lock); }
}
