import os
import json
import configparser
import xxhash
import boto3
from datetime import datetime
from typing import List, Dict, Optional, Set


class S3Uploader:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.s3_client = self._init_s3_client()
        self.report_data = []
        self.processed_files = set()

        # Load exclusion files
        self.dir_exclusions = self._load_json_file(self.config['exclusions']['dir_exclusions'])
        self.file_exclusions = self._load_json_file(self.config['exclusions']['file_exclusions'])
        self.filename_exclusions = self._load_json_file(self.config['exclusions']['filename_exclusions'])

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from INI file"""
        parser = configparser.ConfigParser()
        parser.read(config_path)

        config = {
            's3': dict(parser['S3']),
            'directories': dict(parser['Directories']),
            'extensions': [ext.strip() for ext in parser['Files']['extensions'].split(',')],
            'report': dict(parser['Report']),
            'exclusions': dict(parser['Exclusions'])
        }

        return config

    def _load_json_file(self, filepath: str) -> Set:
        """Load JSON file and return its content as a set"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                return set(data)
        except (FileNotFoundError, json.JSONDecodeError):
            return set()

    def _init_s3_client(self):
        """Initialize S3 client with configured credentials"""
        s3_config = self.config['s3']

        # Yandex Cloud specific validation
        if 'yandexcloud.net' in s3_config['endpoint']:
            if s3_config['region'] not in ('ru-central1', 'ru-central1-a', 'ru-central1-b', 'ru-central1-c'):
                print("Warning: Yandex Cloud region should be ru-central1")

        return boto3.client(
            's3',
            aws_access_key_id=s3_config['access_key'],
            aws_secret_access_key=s3_config['secret_key'],
            endpoint_url=s3_config['endpoint'],
            region_name=s3_config['region']
        )

    def _calculate_xxhash(self, filepath: str) -> str:
        """Calculate xxHash for a file"""
        h = xxhash.xxh64()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()

    def _should_process_file(self, filepath: str, filename: str) -> bool:
        """Check if file should be processed based on exclusions"""
        # Check directory exclusions
        for excluded_dir in self.dir_exclusions:
            if filepath.startswith(excluded_dir):
                return False

        # Check full file path exclusions
        if filepath in self.file_exclusions:
            return False

        # Check filename exclusions
        if filename in self.filename_exclusions:
            return False

        # Check file extension
        ext = os.path.splitext(filename)[1].lower()
        if ext not in self.config['extensions']:
            return False

        return True

    def _generate_s3_key(self, filepath: str) -> str:
        """Generate S3 key for the file"""
        base_dir = self.config['directories']['base_dir']
        relative_path = os.path.relpath(filepath, base_dir)
        return relative_path.replace('\\', '/')

    def _check_s3_connection(self) -> bool:
        """Check connection to S3 bucket"""
        try:
            self.s3_client.head_bucket(Bucket=self.config['s3']['bucket'])
            return True
        except Exception as e:
            print(f"Connection check failed: {e}")
            return False

    def _file_needs_update(self, s3_key: str, local_hash: str) -> bool:
        """Check if file needs to be updated in S3"""
        try:
            response = self.s3_client.head_object(
                Bucket=self.config['s3']['bucket'],
                Key=s3_key
            )
            s3_hash = response.get('Metadata', {}).get('xxhash', '')
            return s3_hash != local_hash
        except:
            # File doesn't exist in S3 or other error
            return True

    def _upload_file_to_s3(self, filepath: str, s3_key: str, file_hash: str) -> bool:
        """Upload file to S3 with metadata"""
        try:
            self.s3_client.upload_file(
                filepath,
                self.config['s3']['bucket'],
                s3_key,
                ExtraArgs={
                    'Metadata': {
                        'xxhash': file_hash,
                        'original_path': filepath
                    }
                }
            )
            return True
        except Exception as e:
            print(f"Failed to upload {filepath}: {e}")
            return False

    def _process_file(self, filepath: str, upload: bool = False) -> Dict:
        """Process a single file"""
        filename = os.path.basename(filepath)

        if not self._should_process_file(filepath, filename):
            return None

        file_hash = self._calculate_xxhash(filepath)
        s3_key = self._generate_s3_key(filepath)

        needs_upload = self._file_needs_update(s3_key, file_hash)
        sent = False

        if upload and needs_upload:
            sent = self._upload_file_to_s3(filepath, s3_key, file_hash)

        file_data = {
            "filePath": filepath,
            "s3code": s3_key,
            "hash": file_hash,
            "date": datetime.now().isoformat(),
            "sent": sent if upload else needs_upload
        }

        return file_data

    def _save_report(self):
        """Save report to JSON file"""
        report_path = self.config['report']['path']
        with open(report_path, 'w') as f:
            json.dump(self.report_data, f, indent=2)

    def _print_extension_stats(self):
        """Print statistics by file extensions"""
        ext_stats = {}
        for item in self.report_data:
            ext = os.path.splitext(item['filePath'])[1].lower()
            if ext not in ext_stats:
                ext_stats[ext] = {'total': 0, 'sent': 0}

            ext_stats[ext]['total'] += 1
            if item.get('sent', False):
                ext_stats[ext]['sent'] += 1

        print("\nFile extension statistics:")
        for ext, stats in ext_stats.items():
            print(f"{ext}: {stats['sent']} sent out of {stats['total']} total")

    def run(self, mode: int):
        """Run the script in specified mode"""
        if mode == 1:
            # Mode 1: Check S3 connection
            if self._check_s3_connection():
                print("Successfully connected to S3 bucket")
            return

        base_dir = self.config['directories']['base_dir']

        # Process all files in the directory tree
        for root, _, files in os.walk(base_dir):
            for filename in files:
                filepath = os.path.join(root, filename)

                if filepath in self.processed_files:
                    continue

                self.processed_files.add(filepath)

                file_data = None

                if mode in [2, 3, 4, 5]:
                    # Modes 2-5: Process files (with or without upload)
                    file_data = self._process_file(filepath, upload=(mode in [3, 4, 5]))

                if file_data:
                    self.report_data.append(file_data)

        # Save and print results
        if mode in [2, 3, 4, 5]:
            self._save_report()
            print(f"Report saved to {self.config['report']['path']}")

            if mode in [4, 5]:
                self._print_extension_stats()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="S3 File Uploader")
    parser.add_argument('--config', required=True, help='Path to configuration INI file')
    parser.add_argument('--mode', type=int, choices=range(1, 6), required=True,
                        help='''Operation mode: 
                       1=Check S3 connection, 
                       2=Prepare report without upload, 
                       3=Upload files with report, 
                       4=Upload with extension stats, 
                       5=Smart update with stats''')

    args = parser.parse_args()

    uploader = S3Uploader(args.config)
    uploader.run(args.mode)