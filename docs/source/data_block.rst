============
Файлы \*.blk
============

Двоичные файлы
--------------

Сводка по содержимому
^^^^^^^^^^^^^^^^^^^^^

bbf
"""

Автономный файл старого формата.

.. code-block:: python

    BbfContent = ...

    BBF = Struct(
        'magic' / Const(b'\x00BBF'),
        'bbf_content' / BbfContent,
    )

bbf_zlib
""""""""

Автономный файл старого формата, сжатый zlib.

.. code-block:: python

    BBF_ZLIB = Struct(
        'magic' / Const(b'\x00BBz'),
        'size' / Int32ul,
        'bbf' / RestreamData(Prefixed(Int32ul, Compressed(GreedyBytes, 'zlib')), BBF),
    )

fat
"""

Автономный файл нового формата.

.. code-block:: python

    FatContent = ...

    FAT = Struct(
        'type' / Const(b'\x01'),
        'fat_content' / FatContent,
    )

fat_zstd
""""""""

Автономный файл нового формата, сжатый zstd.

.. code-block:: python

    ZstdCompressed = ...
    max_output_size = ...

    FAT_ZSTD = Struct(
        'type' / Const(b'\x02'),
        'fat' / RestreamData(Prefixed(Int24ul, ZstdCompressed(GreedyBytes, max_output_size)), FAT),
    )

slim
""""

Разделенный файл нового формата.

.. code-block:: python

    SlimContent = ...

    SLIM = Struct(
        'type' / Const(b'\x03'),
        'slim_content' / SlimContent,
    )

slim_zstd
"""""""""

Разделенный файл нового формата, с сжатый zstd.

.. code-block:: python

    SLIM_ZSTD = Struct(
        'type' / Const(b'\x04'),
        'slim_content' / RestreamData(ZstdCompressed(GreedyBytes, max_output_size), SlimContent),
    )

slim_zstd_dict
""""""""""""""

Разделенный файл нового формата, с сжатый zstd с использованием словаря.

.. code-block:: python

    dict_data = ...

    SLIM_ZSTD_DICT = Struct(
        'type' / Const(b'\x05'),
        'slim_content' / RestreamData(ZstdCompressed(GreedyBytes, max_output_size, dict_data), SlimContent),
    )
