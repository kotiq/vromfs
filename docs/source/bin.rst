=============
BIN контейнер
=============

BIN контейнер содержит обфусцированный и, опционально, сжатый файл.

---------------
Общие структуры
---------------

.. list-table:: Тип заголовка по первым четырем байтам BinHeader.type
    :header-rows: 1
    :align: left

    * - Значение, int32ul
      - Значение, bytes
      - Имя для HeaderType
      - Пояснение
    * - 0x73465256
      - ``b'VRFs'``
      - VRFS
      - Простой заголовок
    * - 0x78465256
      - ``b'VRFx'``
      - VRFX
      - Расширенный заголовок

.. list-table:: Тип платформы по четырем байтам BinHeader.platform
    :header-rows: 1
    :align: left

    * - Значение, int32ul
      - Значение, bytes
      - Имя для PlatformType
    * - 0x43500000
      - ``b'\x00\x00PC'``
      - PC
    * - 0x534f6900
      - ``b'\x00iOS'``
      - IOS
    * - 0x646e6100
      - ``b'\x00and'``
      - ANDROID

.. list-table:: 6 бит параметров упаковки BinHeader.packed.type
    :header-rows: 1
    :align: left
    :widths: 10 10 80

    * - Значение
      - Имя для PackType
      - Пояснение
    * - 0x10
      - ZSTD_OBFS_NOCHECK
      - Образ сжат с zstd и обфусцирован. Контейнер не содержит дайджест образа. ``WarThunder/content/base/res/grp_hdr.vromfs.bin``
    * - 0x20
      - PLAIN
      - Образ записан как есть. Контейнер содержит дайджест образа. ``WarThunder/ui/slides.vromfs.bin``
    * - 0x30
      - ZSTD_OBFS
      - Образ сжат с zstd и обфусцирован. Контейнер содержит дайджест образа. ``WarThunder/char.vromfs.bin``

Параметры упаковки (BinHeader.packed)
=====================================

Параметры упаковки кодируют размер сжатого образа, факт сжатия с обфускацией, а так же наличие дайджеста образа.
Порядок байтов LE.

.. drawio-image:: diagrams/BinHeader.packed.drawio

Type
    Bit(6), параметры упаковки.

Size
    Bit(26), размер сжатого образа. Для несжатого образа равен нулю.

Простой заголовок (BinHeader)
=============================

.. drawio-image:: diagrams/BinHeader.drawio

Type
    BinHeader.type, тип заголовка.

Platform
    BinHeader.platform, тип платформы.

Size
    Int32ul, размер несжатого образа.

Packed
    BinHeader.packed, параметры упаковки.


Расширение заголовка (BinExtHeader)
===================================

Описывается расширение заголовка размером 8 байт.

.. drawio-image:: diagrams/BinExtHeader.drawio

Size
    Int16ul, размер расширения заголовка.

Flags
    Int16ul, поле флагов, неизвестно. Встретились только нули.

Version
    | Int32ul, версия образа.
    | ``1.2.3.4 -> 0x01020304 -> b'\x04\x03\x02\x01'``

-------------------------------------
Общий вид контейнеров (BIN container)
-------------------------------------

Контейнер с простым заголовком (BinHeader).

.. drawio-image:: diagrams/container_with_simple_header.drawio

Контейнер с расширением заголовка (BinHeader + BinExtHeader).

.. drawio-image:: diagrams/container_with_extended_header.drawio

BinHeader
    Простой заголовок

BinExtHeader
    Расширение заголовка

Data
    | Блок данных, содержащий образ.
    | Размер
    |   BinHeader.size для несжатого образа при BinHeader.packed.type = PackType.PLAIN
    |   BinHeader.packed.size для сжатого образа при BinHeader.packed.type из {PackType.ZSTD_OBFS_NOCHECK, PackType.ZSTD_OBFS}

Digest
    | (Bytes(16))?, MD5 дайджест несжатого образа, если есть.
    | Для BinHeader.packed.type из {PackType.PLAIN, PackType.ZSTD_OBFS} дайджест есть.
    | Для BinHeader.packed.type = PackType.ZSTD_OBFS_NOCHECK дайджеста нет.

Extra
    (Bytes(256))?, блок дополнительных данных, если есть.

------------------------------------
Блок данных, содержащий образ (Data)
------------------------------------

Блок данных может содержать сжатый или не сжатый образ. В случае сжатого образа, он так же подвергается обфускации.

Пусть `xor` - побитовое сложение по модулю 2 для блоков.

Способ обфускации:

* Для очень маленьких блоков размером из [0, 15] байт, обфускация не применяется.
* Для маленьких блоков размером из [16, 31]:
    * Для первых 16 байт выполняется `xor` с блоком ``b'55aa55aa0ff00ff055aa55aa48124812'``.
* Для блоков размером от 32 байт:
    * Для первых 16 байт выполняется `xor` с блоком ``b'55aa55aa0ff00ff055aa55aa48124812'``.
    * Для последних 16 байт, начало которых приходится на адрес, кратный 4, выполняется `xor` с блоком ``b'4812481255aa55aa0ff00ff055aa55aa'``.

.. code-block:: text
    :caption: Обфускация блока размером 24 байта.

    0000   FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF   ................
    0010   FF FF FF FF FF FF FF FF                           ........

    0000   AA 55 AA 55 F0 0F F0 0F AA 55 AA 55 B7 ED B7 ED   .U.U.....U.U....
    0010   FF FF FF FF FF FF FF FF                           ........

.. code-block:: text
    :caption: Обфускация блока размером 38 байт.

    0000   FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF   ................
    0010   FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF   ................
    0020   FF FF FF FF FF FF                                 ......

    0000   AA 55 AA 55 F0 0F F0 0F AA 55 AA 55 B7 ED B7 ED   .U.U.....U.U....
    0010   FF FF FF FF B7 ED B7 ED AA 55 AA 55 F0 0F F0 0F   .........U.U....
    0020   AA 55 AA 55 FF FF                                 .U.U..

Сжатие образа происходит по алгоритму Zstandard.

---------------
Примеры разбора
---------------

BIN контейнер с простым заголовком. Образ не сжат, есть дайджест несжатого образа.
==================================================================================

Файл tests/samples/checked_simple_uncompressed_checked.vromfs.bin
-----------------------------------------------------------------

.. drawio-image:: diagrams/checked_simple_uncompressed_checked_dump.drawio

Карта имен
----------

.. list-table::
    :header-rows: 1
    :align: left
    :widths: 20 80

    * - Имя
      - Значение
    * - Header.type
      - BinHeader.VRFS
    * - Header.platform
      - PlatformType.PC
    * - Header.size
      - 848
    * - Header.packed
      - | type = PackType.PLAIN
        | size = 0
    * - Digest
      - 4c03d79dacf82145ca21a52b37d6b9f1

BIN контейнер с расширением заголовка. Образ сжат, есть дайджест несжатого образа.
==================================================================================

Файл tests/samples/unchecked_extended_compressed_checked.vromfs.bin
-------------------------------------------------------------------

.. drawio-image:: diagrams/unchecked_extended_compressed_checked_dump.drawio

Карта имен
----------

.. list-table::
    :header-rows: 1
    :align: left
    :widths: 20 80

    * - Имя
      - Значение
    * - Header.type
      - BinHeader.VRFX
    * - Header.platform
      - PlatformType.PC
    * - Header.size
      - 752
    * - Header.packed
      - | type = PackType.ZSTD_OBFS
        | size = 621
    * - ExtHeader.size
      - 8
    * - ExtHeader.flags
      - 0
    * - ExtHeader.version
      - 1.2.3.4
    * - Digest
      - 18b4123bda1259f3b17d1cc2c14a96dd
