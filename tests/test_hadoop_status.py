"""Hadoop execution claims must be tied to the current raw and cleaned dataset."""
import hashlib
import io
from contextlib import redirect_stdout
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from backend import main, pipeline


class HadoopStatusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.processed = self.root / 'processed'
        self.raw = self.root / 'raw'
        self.processed.mkdir()
        self.raw.mkdir()
        self.dataset = self.processed / 'weather.parquet'
        self.dataset.write_bytes(b'isolated cleaned dataset')
        (self.raw / 'Hyderabad.csv').write_bytes(b'city,time\nHyderabad,2025-01-01\n')
        self.evidence = {
            'status': 'verified', 'parity_passed': True,
            'dataset_sha256': hashlib.sha256(self.dataset.read_bytes()).hexdigest(),
            'raw_checksums': [{'name': 'Hyderabad.csv', 'sha256': hashlib.sha256((self.raw / 'Hyderabad.csv').read_bytes()).hexdigest()}],
            'engine': 'Apache Hadoop test execution', 'execution_mode': 'LocalJobRunner',
            'generated_at': '2026-10-08T00:00:00+00:00', 'input_rows': 1, 'clean_rows': 1,
            'monthly_groups': 1, 'comparison': {'passed': True, 'compared_groups': 1},
            'hdfs': {'input_path': '/weather/raw', 'output_path': '/weather/output'},
        }
        self.patches = [patch.object(main, 'PROCESSED', self.processed), patch.object(main, 'RAW', self.raw, create=True)]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        main.dataset_hash.cache_clear()
        self.addCleanup(main.dataset_hash.cache_clear)

    def write_evidence(self, updates=None):
        evidence = dict(self.evidence)
        if updates:
            evidence.update(updates)
        (self.processed / 'hadoop_evidence.json').write_text(json.dumps(evidence), encoding='utf-8')

    def status(self):
        result = main.pipeline_status()
        self.assertIn('hadoop_verified', result)
        return result

    def test_current_success_exposes_evidence_and_hadoop_stages(self):
        self.write_evidence()
        result = self.status()
        self.assertTrue(result['hadoop_verified'])
        self.assertEqual(result['hadoop_evidence']['execution_mode'], 'LocalJobRunner')
        stages = {stage['name']: stage['status'] for stage in result['steps']}
        self.assertEqual(stages['HDFS'], 'verified')
        self.assertEqual(stages['Hadoop MapReduce'], 'verified')
        self.assertIn('hadoop_evidence.json', [artifact['name'] for artifact in result['artifacts']])

    def test_absent_or_failed_evidence_never_verifies(self):
        for updates in [None, {'status': 'failed'}, {'parity_passed': False}, {'parity_passed': 'true'}]:
            with self.subTest(updates=updates):
                if updates is not None:
                    self.write_evidence(updates)
                result = self.status()
                self.assertFalse(result['hadoop_verified'])
                self.assertNotIn('hadoop_evidence', result)

    def test_changed_cleaned_dataset_invalidates_proof(self):
        self.write_evidence()
        self.dataset.write_bytes(b'a changed cleaned dataset')
        self.assertFalse(self.status()['hadoop_verified'])

    def test_changed_added_or_deleted_raw_csv_invalidates_proof(self):
        self.write_evidence()
        raw_path = self.raw / 'Hyderabad.csv'
        original = raw_path.read_bytes()
        for mutation in ['changed', 'added', 'deleted']:
            with self.subTest(mutation=mutation):
                raw_path.write_bytes(original)
                (self.raw / 'Delhi.csv').unlink(missing_ok=True)
                if mutation == 'changed':
                    raw_path.write_bytes(b'different source records')
                elif mutation == 'added':
                    (self.raw / 'Delhi.csv').write_bytes(b'additional source city')
                else:
                    raw_path.unlink()
                self.assertFalse(self.status()['hadoop_verified'])

    def test_missing_checksums_or_cleaned_dataset_never_verifies(self):
        self.write_evidence({'raw_checksums': {}})
        self.assertFalse(self.status()['hadoop_verified'])
        self.write_evidence()
        self.dataset.unlink()
        self.assertFalse(self.status()['hadoop_verified'])

    def test_inconsistent_or_partial_execution_details_never_verify(self):
        invalid = [
            {'comparison': {'passed': False}}, {'comparison': {}},
            {'comparison': {'passed': 'true'}},
            {'clean_rows': 0}, {'clean_rows': True}, {'clean_rows': None},
            {'monthly_groups': 0}, {'monthly_groups': 1.5},
            {'hdfs': {}}, {'hdfs': None},
            {'hdfs': {'input_path': 'relative/raw', 'output_path': '/weather/output'}},
            {'hdfs': {'input_path': '/weather/raw', 'output_path': '/'}},
        ]
        for updates in invalid:
            with self.subTest(updates=updates):
                self.write_evidence(updates)
                self.assertFalse(self.status()['hadoop_verified'])

    def test_corrupt_evidence_is_unverified_without_breaking_pipeline(self):
        for content in ['{broken', '[]', 'null']:
            with self.subTest(content=content):
                (self.processed / 'hadoop_evidence.json').write_text(content)
                self.assertFalse(self.status()['hadoop_verified'])


class HadoopRefreshTests(unittest.TestCase):
    def test_reprocessing_removes_old_hadoop_execution_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw, processed = root / 'raw', root / 'processed'
            raw.mkdir(); processed.mkdir()
            (raw / 'Hyderabad.csv').write_text('city,time,temperature,humidity,precipitation,wind_speed,latitude,longitude\nHyderabad,2025-01-01T00:00:00,25,50,0,10,17.4,78.4\n')
            proof = processed / 'hadoop_evidence.json'
            proof.write_text('{"status":"verified"}')
            with patch.object(pipeline, 'RAW', raw), patch.object(pipeline, 'PROCESSED', processed), redirect_stdout(io.StringIO()):
                pipeline.run_pipeline()
            self.assertFalse(proof.exists())


if __name__ == '__main__':
    unittest.main()
