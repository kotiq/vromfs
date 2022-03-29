import pytest


@pytest.fixture(scope='module')
def checked_vromfs_container(paths, digests):
    return {
        'names_header': {
            'offset': 0x30,
            'count': 2,
        },
        'data_header': {
            'offset': 0x50,
            'count': 2,
        },
        'digests_header': {
            'end': 0x98,
            'begin': 0x70,
        },
        'names_info': [0x40, 0x47],
        'names_data': paths,
        'data_info': [
            {'offset': 0xa0, 'size': 2},
            {'offset': 0xb0, 'size': 0x0c},
        ],
        'digests_data': digests,
        'offset': 0xa0,
    }


@pytest.fixture(scope='module')
def unchecked_vromfs_container(paths):
    return {
        'names_header': {
            'offset': 0x20,
            'count': 2,
        },
        'data_header': {
            'offset': 0x40,
            'count': 2,
        },
        'digests_header': None,
        'names_info': [0x30, 0x37],
        'names_data': paths,
        'data_info': [
            {'offset': 0x60, 'size': 2},
            {'offset': 0x70, 'size': 0x0c},
        ],
        'digests_data': None,
        'offset': 0x60,
    }


@pytest.fixture(scope='module')
def unchecked_ex_vromfs_container(paths):
    return {
        'names_header': {
            'offset': 0x30,
            'count': 2,
        },
        'data_header': {
            'offset': 0x50,
            'count': 2,
        },
        'digests_header': {
            'end': 0x70,
            'begin': 0x00,
        },
        'names_info': [0x40, 0x47],
        'names_data': paths,
        'data_info': [
            {'offset': 0x70, 'size': 2},
            {'offset': 0x80, 'size': 0x0c},
        ],
        'digests_data': None,
        'offset': 0x70,
    }
