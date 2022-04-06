# Инструмент для работы с файлами контейнеров и образов VROMFS.

> :warning: Функции упаковки образов и контейнеров приведены только для создания тестовых данных.

## Среда выполнения

Linux, Python 3.7. Распаковщик однопоточный, рекомендую PyPy 7.3.8.

## Установка

```shell
git clone https://github.com/kotiq/vromfs
cd vromfs 
pip install .
```

## Распаковка файлов

Пример распаковщика `src/vromfs/demo/vromfs_bin_unpacker.py`.

Распаковщик работает в двух режимах: распаковка файлов и получение сводки о файлах в образе. 
В зависимости от режима, схема выходного параметра различается.

### Получение сводки о файлах в образе

```shell
vromfs_bin_unpacker --metadata
                    [--input_filelist MAYBE_IN_FILES]
                    [-o MAYBE_OUT_PATH]
                    input
```

Аргументы:

- `--metadata` Режим получения сводки о файлах.
- `--input_filelist` Файл с JSON списком файлов, `-` для чтения из `stdin`. Если не указан, запросить сводку для всех 
файлов из образа.
- `-о, --output` Выходной файл. Если не указан, вывести в `stdout`.
- `input` Файл .vromfs.bin контейнера.

Пример запроса сводки о файлах `config/wpcost.blk`, `version`, `nop` из контейнера `char.vromfs.bin`. 
Файл `nop` отсутствует в образе.

```shell
echo '["config/wpcost.blk", "version", "nop"]' |\
vromfs_bin_unpacker --metadata --input_filelist - ~/games/WarThunder/char.vromfs.bin |\
python -m json.tool
```

Выходной файл:

- `version` Версия схемы.
- `filelist` Словарь {Имя => SHA1 дайджест}.
- `~filelist` Список отсутствующих файлов из входного списка.

```json
{
    "version": "1.1",
    "filelist": {
        "config/wpcost.blk": "c9fa212c3fcad93dd3fec78d80b084ee06dd7fe0",
        "version": "91fd47a80f1984d65402a2c5de2031515d781c0c"
    },
    "~filelist": [
        "nop"
    ]
}
```

### Распаковка файлов

```shell
vromfs_bin_unpacker [--format {RAW,STRICT_BLK,JSON,JSON_2,JSON_3}]
                    [--sort]
                    [--input_filelist MAYBE_IN_FILES]
                    [-x]
                    [-o MAYBE_OUT_PATH]
                    input
```

Аргументы:

- `--format` Формат выходного блока, не зависит от регистра. `Raw`: распаковать как есть. По умолчанию `json`.
- `--sort` Сортировать ключи для форматов `json`, `json_2`, `json_3`.
- `--input_filelist` Файл с JSON списком файлов, `-` для чтения из `stdin`. Если не указан, распаковать все файлы из 
образа.
- `-x, --exitfirst` Закончить распаковку при первой ошибке.
- `-o, --output` Родитель для выходной директории, выходная директория - имя контейнера. Если не указан, `cwd`, 
выходная директория - имя контейнера с постфиксом `_u`.
- `input` Файл .vromfs.bin контейнера.

Пример распаковки файлов `config/wpcost.blk`, `version`, `nop` из контейнера `char.vromfs.bin`.
Файл `nop` отсутствует в образе.

```shell
echo '["config/wpcost.blk", "version", "nop"]' |\
vromfs_bin_unpacker --input_filelist - -o /tmp --format strict_blk ~/games/WarThunder/char.vromfs.bin
```

Вывод:

```
1649101539.0282645 INFO Начало распаковки.
1649101539.0303192 ERROR [FAIL] '/home/kotiq/games/WarThunder/char.vromfs.bin'::'nop': "Нет FileInfo, содержащего путь 'nop'"
1649101550.4968865 DEBUG 'config/wpcost.blk': SLIM_ZST => STRICT_BLK
1649101550.5555458 DEBUG 'version'
1649101550.5556657 INFO Успешно распаковано: 2/3.
1649101550.5557013 ERROR Ошибка при обработке файлов.
```

Дерево файлов:

```
$ tree -s --metafirst /tmp/char.vromfs.bin
[         80]  /tmp/char.vromfs.bin
[         60]  ├── config
[   13003236]  │   └── wpcost.blk
[          9]  └── version
```
