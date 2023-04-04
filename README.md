# Инструмент для работы с файлами контейнеров и образов VROMFS.

## Среда выполнения

Linux, Python 3.7. Распаковщик однопоточный, рекомендую PyPy 7.3.8.

## Установка

```shell
git clone https://github.com/kotiq/vromfs
cd vromfs 
pip install .
```

## Сборка документации

Диаграммы построены с использованием [drawio](https://github.com/jgraph/drawio-desktop/)

```shell
pip install -r requirements-docs.txt
python setup.py build_sphinx
```

## Распаковка файлов

Пример распаковщика `src/vromfs/demo/vromfs_bin_unpacker.py`.

Распаковщик работает в двух режимах: распаковка файлов и получение сводки о файлах в образе. 
В зависимости от режима, схема выходного параметра различается.

### Получение сводки о файлах в образе

```shell
vromfs_bin_unpacker [-h]
                    --metadata
                    [--input_filelist MAYBE_IN_FILES]
                    [-o MAYBE_OUT_PATH]
                    input
```

Аргументы:

- `-h, --help` Показать справку.
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
vromfs_bin_unpacker [--format {json,json_2,json_3,raw,strict_blk}]
                    [--sort]
                    [--input_filelist MAYBE_IN_FILES]
                    [-x]                    
                    [-o MAYBE_OUT_PATH]
                    [--loglevel {critical,error,warning,info,debug}]
                    input
```

Аргументы:

- `--format` Формат выходного блока, не зависит от регистра. `raw`: распаковать как есть. По умолчанию `json`.
- `--sort` Сортировать ключи для форматов `json`, `json_2`, `json_3`.
- `--minify` Минифицировать JSON*.
- `--input_filelist` Файл с JSON списком файлов, `-` для чтения из `stdin`. Если не указан, распаковать все файлы из 
образа.
- `-x, --exitfirst` Закончить распаковку при первой ошибке.
- `-o, --output` Родитель для выходной директории, выходная директория - имя контейнера. Если не указан, `cwd`, 
выходная директория - имя контейнера с постфиксом `_u`.
- `--loglevel` Уровень сообщений из `critical`, `error`, `warning`, `info`, `debug`. По умолчанию `info`.
- `input` Файл .vromfs.bin контейнера.

Пример распаковки файлов `config/wpcost.blk`, `version`, `nop` из контейнера `char.vromfs.bin`.
Файл `nop` отсутствует в образе.

```shell
echo '["config/wpcost.blk", "version", "nop"]' |\
vromfs_bin_unpacker --input_filelist - -o /tmp --format strict_blk ~/games/WarThunder/char.vromfs.bin
```
```text
1649101539.0282645 INFO Начало распаковки.
1649101539.0303192 ERROR [FAIL] '/home/kotiq/games/WarThunder/char.vromfs.bin'::'nop': "Нет FileInfo, содержащего путь 'nop'"
1649101550.4968865 DEBUG 'config/wpcost.blk': SLIM_ZST => STRICT_BLK
1649101550.5555458 DEBUG 'version'
1649101550.5556657 INFO Успешно распаковано: 2/3.
1649101550.5557013 ERROR Ошибка при обработке файлов.
```

Дерево файлов:

```shell
$ tree -s --metafirst /tmp/char.vromfs.bin
```
```text
[         80]  /tmp/char.vromfs.bin
[         60]  ├── config
[   13003236]  │   └── wpcost.blk
[          9]  └── version
```

## Упаковка файлов

Пример упаковщика `src/vromfs/demo/vromfs_bin_packer.py`.

Упаковщик приведен, главным образом, как генератор тестовых данных. 
Предполагается, что для файлов blk перевод в двоичный формат произведен заранее, если это необходимо.

```shell
 vromfs_bin_packer [-h]
                   [-v VERSION]
                   [--compressed] 
                   [--checked]
                   [-o OUT_PATH] 
                   in_path
```

Аргументы:

- `-h, --help` Показать справку.
- `-v, --ver` Версия архива x.y.z.w, где x, y, z, w из 0 .. 255. 
- `--compressed` Сжать образ.
- `--checked` Добавить дайджест несжатого образа.
- `-o, --output` Выходной файл. По умолчанию `./out.vromfs.bin`. 
- `in_path` Директория для упаковки.

Если не указаны ни checked ни compressed, применяются оба аргумента.

В контейнер попадают файлы, перечисленные в директории, но не сама директория. 

Пример упаковки файлов из директории `/tmp/files` в архив `/tmp/out.vromfs.bin` версии `1.2.3.4`.

Дерево файлов:

```shell
tree -s --metafirst /tmp/files
```
```text
[         80]  /tmp/files
[         60]  ├── inner
[       1061]  │   └── fstab
[        106]  └── lsb-release
```

Формирование архива:

```shell
vromfs_bin_packer.py -v 1.2.3.4 -o /tmp/out.vromfs.bin /tmp/files
```
```text
1655019014.6393943 DEBUG /tmp/files => temp vromfs
1655019014.6394637 DEBUG Размер временного образа: 1296
1655019014.640162 DEBUG temp vromfs => /tmp/out.vromfs.bin
1655019014.640218 INFO /tmp/files => /tmp/out.vromfs.bin
```

Содержимое архива:

```shell
vromfs_bin_unpacker.py --metadata /tmp/out.vromfs.bin |\
python -m json.tool
```
```json
{
    "version": "1.1",
    "filelist": {
        "inner/fstab": "a0940cb3f3298ae0cb9ba0a30e05e678e7f8c6f2",
        "lsb-release": "792f608be04167807db067707a31a656aa687d0f"
    }
}
```
