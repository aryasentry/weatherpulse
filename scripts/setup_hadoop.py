"""Install official Apache Hadoop 3.5.0 only inside this project's .runtime.

Usage: python scripts/setup_hadoop.py
Downloads the official binary (~hundreds of MB), checks its Apache SHA512,
and extracts without traversing outside .runtime. Does not install Java,
change global packages, start SSH, or format an HDFS directory.
Optional Hadoop requires a whitespace-free full project path.
After first installation, repeat setup verifies the cached digest offline.
"""
import argparse
import hashlib
import json
import re
import ssl
import certifi
import tarfile
import urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'.runtime'
VERSION='3.5.0'
BASE=f'https://downloads.apache.org/hadoop/common/hadoop-{VERSION}'
ARCHIVE_URL=f'https://dlcdn.apache.org/hadoop/common/hadoop-{VERSION}/hadoop-{VERSION}.tar.gz'
CHECKSUM_URL=f'{BASE}/hadoop-{VERSION}.tar.gz.sha512'


def verify_checksum(path, checksum_text):
    matches=re.findall(r'\b[0-9a-fA-F]{128}\b',checksum_text)
    if len(matches)!=1: raise ValueError('Apache SHA512 response must contain exactly one digest')
    with open(path,'rb') as source: digest=hashlib.file_digest(source,'sha512').hexdigest()
    if digest.lower()!=matches[0].lower(): raise ValueError('Downloaded archive SHA512 does not match Apache checksum; extraction refused')
    return digest


def safe_extract(path,target):
    target=Path(target); target.mkdir(parents=True,exist_ok=True); resolved=target.resolve()
    with tarfile.open(path,'r:gz') as archive:
        for member in archive.getmembers():
            destination=(resolved/member.name).resolve()
            if not destination.is_relative_to(resolved): raise ValueError('Unsafe archive member traverses outside runtime directory')
        archive.extractall(target,filter='data')


def check_project_path(root):
    if any(character.isspace() for character in str(root)):
        raise RuntimeError('Optional Hadoop requires a project path without spaces. Move/rename it to a whitespace-free full path, for example ~/Projects/Weather_Data_Analysis. The normal dashboard still supports paths with spaces.')


def setup():
    check_project_path(ROOT)
    downloads=RUNTIME/'downloads'; downloads.mkdir(parents=True,exist_ok=True)
    path=downloads/f'hadoop-{VERSION}.tar.gz'
    destination=RUNTIME/f'hadoop-{VERSION}'; receipt_path=RUNTIME/'hadoop-download.json'
    if path.is_file() and (destination/'bin'/'hdfs').is_file() and receipt_path.is_file():
        receipt=json.loads(receipt_path.read_text())
        if receipt.get('version')==VERSION:
            verify_checksum(path,receipt.get('sha512',''))
            print('Previously verified Hadoop archive rechecked; using local installation offline.',flush=True)
            return destination
    tls=ssl.create_default_context(cafile=certifi.where())
    checksum=urllib.request.urlopen(CHECKSUM_URL,timeout=60,context=tls).read().decode()
    (downloads/(path.name+'.sha512')).write_text(checksum)
    if not path.is_file():
        temp=path.with_suffix('.gz.part')
        print(f'Downloading {ARCHIVE_URL} into project .runtime',flush=True)
        with urllib.request.urlopen(ARCHIVE_URL,timeout=120,context=tls) as response, temp.open('wb') as output:
            total=int(response.headers.get('Content-Length',0)); read=0; last=0
            while chunk:=response.read(1024*1024):
                output.write(chunk); read+=len(chunk)
                if read-last>=50*1024*1024: print(f'Downloaded {read//(1024*1024)} MiB'+(f' of {total//(1024*1024)} MiB' if total else ''),flush=True); last=read
        temp.replace(path)
    digest=verify_checksum(path,checksum); destination=RUNTIME/f'hadoop-{VERSION}'
    if not (destination/'bin'/'hdfs').is_file():
        print('SHA512 verified; extracting project-local Hadoop...',flush=True); safe_extract(path,RUNTIME)
    receipt={'version':VERSION,'archive_url':ARCHIVE_URL,'checksum_url':CHECKSUM_URL,'sha512':digest,'installation':str(destination)}
    (RUNTIME/'hadoop-download.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt),flush=True)
    return destination

if __name__=='__main__':
    argparse.ArgumentParser(description=__doc__).parse_args(); setup()
