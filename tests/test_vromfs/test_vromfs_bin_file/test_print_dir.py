def test_print_dir(checked_compressed_file):
    print(f'\npath: {repr(str(checked_compressed_file.path))}')
    checked_compressed_file.print_dir()
