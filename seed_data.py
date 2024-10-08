#!/usr/bin/env python3
"""Seed data from anonymized OSCE notes saved as text files.
    ©2024, Ovais Quraishi
"""

import hashlib
import json
import random
from pathlib import Path
import sys
sys.path.insert(0, str(Path('../').resolve()))

from database import insert_data_into_table
from database import get_select_query_result_dicts
from encryption import encrypt_text
from utils import gen_internal_id, ts_int_to_dt_obj


def get_localities():
    """Get localities from the codes_document data
        this will be used to seed data
    """

    localities = []

    sql_query = """select
                       codes_document ->> 'locality'
                       as locality
                   from
                       cpt_hcpcs_codes;
                """

    # list of dicts
    dicts = get_select_query_result_dicts(sql_query)
    # list of localities
    localities = list(item['locality'] for item in dicts)
    return localities

def get_filenames(extension, directory):
    """Retrieve filenames with a specific extension from a given directory.

		Parameters:
			extension (str): The file extension to filter files by.
			directory (str): The directory to search for files in.

		Returns:
			list: A list of Path objects representing filenames with the
					given extension in the directory.
    """

    files = list(Path('./' + directory).glob('*.' + extension))
    return files

def read_file(filename):
    """Read the content of a file.

		Parameters:
			filename (str): The name of the file to read.

		Returns:
			str: The content of the file.
			
		Raises:
			FileNotFoundError: If the specified file does not exist.
    """

    file = Path(filename)
    if not file.exists():
        raise FileNotFoundError("File not found: {filename}")
    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def file_to_db(encrypt_analysis=False):
    """Read files, process their content, and insert data into the database.

		Parameters:
			encrypt_analysis (bool, optional): Whether to encrypt the content
			before inserting it into the database. Defaults to False.
    """

    dt = ts_int_to_dt_obj()
    pt_localities = get_localities()
    all_files = get_filenames('txt', 'MedData/Clean Transcripts')
    if all_files:
        for a_file in all_files:
            print(a_file)
            source = 'file'
            category = 'OSCE'
            patient_id = gen_internal_id()
            content = read_file(a_file)
            content_sha512 = hashlib.sha512(str.encode(content)).hexdigest()
            if encrypt_analysis:
                content = encrypt_text(content).decode('utf-8')
            patient_note_document = {
                                'schema_version' : '1',
                                'source' : source,
                                'category' : category,
                                'patient_id' : patient_id,
                                'locality' : random.choice(pt_localities),
                                'note' : content.replace('\u0000','')
                                }
            patient_note_data = {
                            'timestamp': dt,
                            'patient_id' : patient_id,
                            'patient_note_id' : content_sha512,
                            'patient_note' : json.dumps(patient_note_document)
                            }
            insert_data_into_table('patient_notes', patient_note_data)

file_to_db(True)
