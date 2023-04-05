================
VROMFS контейнер
================

VROMFS контейнер содержит дерево файлов.

В качестве примера закодирована директория:

.. code-block:: text

    [4.0K]  .
    ├── [ 256]  78e3c1b3484d1c058678f121ecebef275f7e64a99b28320f73dba970097e1bb5.dict
    ├── [4.0K]  config
    │   └── [  85]  section_slim_zst_dict.blk
    ├── [ 124]  nm
    └── [   8]  version

---------------
Общие структуры
---------------

Имя
===

---------------------------------------
Общий вид контейнера (VROMFS Container)
---------------------------------------

Контейнеры различаются адресу начала таблицы имен и по адресу начала таблицы дайджестов.
Встретились три типа контейнеров:

* | Начало таблицы адресов имен 0x20. Образ не содержит ни заголовка дайджестов, ни таблицы дайджестов.
  | Образ из ``WarThunder/aces.vromfs.bin``
* Начало таблицы адресов имен 0x30. Образ содержит заголовок таблицы дайджестов.
    * | Начало таблицы дайджестов 0x00. Образ не содержит таблицы дайджестов.
      | Образ из ``Enlisted/content/enlisted/fonts.vromfs.bin``
    * | Начало таблицы дайджестов отлично от 0x00. Образ содержит таблицу дайджестов.
      | Образ из ``WarThunder/ui/fonts.vromfs.bin``

Контейнер состоит из блоков Names Header, Data Header, Digests Header, Names Info, Names Data, Data Info, Digests Data,
Data. Размер каждого из них - наименьшее число, кратное 16.

Элементы результирующих таблиц из блока адресов имен (Names Info), блока адресов данных (Data Info) и
блока дайджестов (Digests Data) связаны по порядку обхода контейнера от начала:
{(NamesInfo[0], DataInfo[0], DigestsData[0]), ..., (NamesInfo[N], DataInfo[N], DigestsData[N])}

.. drawio-image:: diagrams/image.drawio

Заголовок таблицы имен (Names Header)
=====================================

Offset
    Int32ul, адрес блока адресов имен (Names Info).

Count
    Int32ul, количество имен.

Заголовок таблицы данных (Data Header)
======================================

Offset
    Int32ul, адрес блока адресов данных (Data Info).

Count
    Int32ul, количество адресов данных.

Заголовок таблицы дайджестов (Digests Header)
=============================================

End
    Int64ul, конец таблицы дайджестов (Digests Table).

Begin
    Int64ul, Начало таблицы дайджестов.

Блок адресов имен (NamesInfo)
=============================

Массив адресов Name Offset.

Name Offset
    Int64ul, адрес имени в блоке имен (Names Data)

Блок имен (Names Data)
======================

Блок имен Name.

Name
    | CString, относительное имя файла.
    | Файл таблицы имен ``nm`` кодируется как ``b'\xff\x3fnm'``.

Блок описания данных (Data Info)
================================

Блок пар Datum Info = (Offset, Size). Адрес каждого элемента - наименьшее число, кратное 16.

Offset
    Int32ul, начало блока данных (Datum).

Size
    Int32ul, размер блока данных в байтах.

Блок таблицы дайджестов (Digests Data)
======================================

Массив дайджестов данных Datum Digest.

Datum Digest
    Byte[20], sha1 дайджест блока данных Datum.

Блок данных (Data)
==================

Последовательность блоков данных (Datum). Адрес каждого элемента - наименьшее число, кратное 16.

Datum
    Bytes, содержимое файла. Адрес и размер описываются структурой Datum Info.


--------------
Пример разбора
--------------

VROMFS контейнер с блоком дайджестов.
=====================================

Файл tests/samples/checked.vromfs
---------------------------------

.. drawio-image:: diagrams/checked_dump.drawio

Names Header
------------

.. list-table::
    :header-rows: 1
    :align: left

    * - Имя
      - Значение
    * - NamesHeader.offset
      - 0x30
    * - NamesHeader.count
      - 4

Data Header
-----------

.. list-table::
    :header-rows: 1
    :align: left

    * - Имя
      - Значение
    * - DataHeader.offset
      - 0xd0
    * - DataHeader.count
      - 4

Digests Header
--------------

.. list-table::
    :header-rows: 1
    :align: left

    * - Имя
      - Значение
    * - DigestsHeader.end
      - 0x160
    * - DigestsHeader.begin
      - 0x110

Names Info и Names Data
-----------------------

.. list-table::
    :header-rows: 1
    :align: left
    :widths: 10 10 80

    * - Индекс
      - Адрес
      - Имя, bytes
    * - 0
      - 0x50
      - ``b'78e3c1b3484d1c058678f121ecebef275f7e64a99b28320f73dba970097e1bb5.dict'``
    * - 1
      - 0x96
      - ``b'config/section_slim_zst_dict.blk'``
    * - 2
      - 0xb7
      - ``b'version'``
    * - 3
      - 0xbf
      - ``b'\xff\x3fnm'``

Data Info и Digests Data
------------------------

.. list-table::
    :header-rows: 1
    :align: left
    :widths: 10 10 10 70

    * - Индекс
      - Адрес
      - Размер, байт
      - Дайджест
    * - 0
      - 0x160
      - 0x100
      - 99d377db24e9be5472d2e22d54e0b78758386e63
    * - 1
      - 0x260
      - 0x55
      - c4d93837dafb4b8bcdfbe4c2cfc158e8f604a7de
    * - 2
      - 0x2c0
      - 0x8
      - b504fbe3288b557afafb6582de89a30409e155f1
    * - 3
      - 0x2d0
      - 0x7c
      - 2352af8bcac8e2106afc86f0893bc36ec106c882

Карта имен
----------

.. list-table::
    :header-rows: 1
    :align: left
    :widths: 10 35 10 10 35

    * - Индекс
      - Имя, bytes
      - Адрес
      - Размер, байт
      - Дайджест
    * - 0
      - ``b'78e3c1b3484d1c058678f121ecebef275f7e64a99b28320f73dba970097e1bb5.dict'``
      - 0x160
      - 256
      - 99d377db24e9be5472d2e22d54e0b78758386e63
    * - 1
      - ``b'config/section_slim_zst_dict.blk'``
      - 0x260
      - 85
      - c4d93837dafb4b8bcdfbe4c2cfc158e8f604a7de
    * - 2
      - ``b'version'``
      - 0x2c0
      - 8
      - b504fbe3288b557afafb6582de89a30409e155f1
    * - 3
      - ``b'\xff\x3fnm'``
      - 0x2d0
      - 124
      - 2352af8bcac8e2106afc86f0893bc36ec106c882
