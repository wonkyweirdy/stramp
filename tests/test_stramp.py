"""
Tests at the CLI command level
"""

import filecmp
import json
import os
import time
from pathlib import Path
from unittest import mock

from click.testing import CliRunner

from stramp.cli import main


org_sample_1_hashes = [
    [0, 2427, '6b29201f695a0a1ec220461b8625f54ab1c6ef0719c996189c951e495938dcde'],
    [0, 1888, 'ae97612ceb89f27cde8e7eb62143519a2baf42127e80e077074d2a8346bf574f'],
    [556, 1226, '3cb5bf82bf7628cd59cca5ccaa39529b6c09bf033ce83fc1826a5ff000778c9f'],
    [1226, 1888, 'ddb0067c83050c79412c68792d34f521626fea78fbd15139250e78cde2ce25b1'],
    [1420, 1888, '94db30754e12494233a9ad69f2e31537c79bea1dfe5c0d9128f8adcea48e49bd'],
    [1888, 2427, '535ab546235c12c78fcf8849fd5cd748bf4a11bc26edae1bb7d38fd903dae547']]


def test_help():
    runner = CliRunner()
    result = runner.invoke(main, '--help')
    assert result.exit_code == 0


def test_hash_only():

    sample_file = os.path.join(os.path.dirname(__file__), 'org-sample-1.txt')

    runner = CliRunner()
    with runner.isolated_filesystem():

        with mock.patch('stramp.paths.paths.app_dir_path', Path(os.getcwd())):
            result = runner.invoke(main, ['--hash-only', sample_file])
            assert result.exit_code == 0
            d = json.loads(result.stdout)
            assert len(d) == 2
            assert d['generator'] == 'stramp'
            assert len(d['documents']) == 1
            assert d['documents'][0]['range_hashes'] == org_sample_1_hashes


def test_hash():

    sample_file_1 = os.path.join(os.path.dirname(__file__), 'org-sample-1.txt')
    sample_file_2 = os.path.join(os.path.dirname(__file__), 'org-sample-2.txt')

    runner = CliRunner()
    with runner.isolated_filesystem():

        config = {
            'documents': [
                dict(path=sample_file_1, format='org'),
                dict(path=sample_file_2, format='org'),
            ]
        }

        with open('config.json', 'w', encoding='UTF-8') as f:
            json.dump(config, f)

        with mock.patch('stramp.paths.paths.app_dir_path', Path(os.getcwd())), \
                mock.patch('subprocess.call', autospec=True) as mock_run:

            def run_ots(args, **kw):

                if args[1] == 'stamp':
                    with open(args[2] + '.ots', 'wb') as ff:
                        ff.write(b'FAKE-STAMP')
                    return 0

                assert args[1] == 'upgrade'
                os.rename(args[2], args[2] + '.bak')
                with open(args[2], 'wb') as ff:
                    ff.write(b'FAKE-UPGRADED-STAMP')
                return 0

            mock_run.side_effect = run_ots

            # Generate the JSON hash file and (mock) stamp it with "ots stamp".
            result = runner.invoke(main, ['--hash'], catch_exceptions=False)

            assert result.exit_code == 0
            assert result.output == ''

            assert set(os.listdir('.')) == {'config.json', 'data', 'new', 'stamped', 'complete'}

            data_names = sorted(os.listdir('data'))
            assert len(data_names) == 2

            assert filecmp.cmp(
                os.path.join('data', data_names[0]),
                sample_file_1)

            assert filecmp.cmp(
                os.path.join('data', data_names[1]),
                sample_file_2)

            assert not os.listdir('new')

            stamped_names = os.listdir('stamped')
            assert len(stamped_names) == 2

            if stamped_names[0].endswith('.json'):
                hash_name = stamped_names[0]
            else:
                hash_name = stamped_names[1]

            assert mock_run.call_count == 1

            # Backdate the stamp file so it looks older than the minimum age for processing
            t = time.time() - 24 * 3600
            os.utime(os.path.join('stamped', hash_name + '.ots'), (t, t))

            # Process the generated stamp file. This should (mock) "ots upgrade" the stamp file.
            result = runner.invoke(main, ['--process'], catch_exceptions=False)

            assert result.exit_code == 0
            assert result.output == ''

            assert not os.listdir('new')
            assert not os.listdir('stamped')

            assert set(os.listdir('complete')) == {
                hash_name,
                hash_name + '.ots',
                hash_name + '.ots.bak',
            }

            assert Path('complete', hash_name + '.ots').read_bytes() == b'FAKE-UPGRADED-STAMP'
            assert Path('complete', hash_name + '.ots.bak').read_bytes() == b'FAKE-STAMP'

            d = json.loads(Path('complete', hash_name).read_bytes())
            assert d['documents'][0]['range_hashes'] == org_sample_1_hashes
