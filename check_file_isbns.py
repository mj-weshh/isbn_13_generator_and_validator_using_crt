#!/usr/bin/env python3
import re
import sys
from isbn13_crt import check_isbn

def check_file_isbns(filename):
    """
    Verify all ISBNs in a file follow the CRT rules
    """
    print(f"Checking ISBNs in file: {filename}")
    
    # Read the file
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Extract ISBNs
    isbns = []
    for line in lines:
        # Match lines like "1. 9783160001071 (Format: 978-3-16-0001071)"
        if re.match(r'^\d+\.\s+\d{13}\s+\(Format:', line):
            isbn = line.split('. ')[1].split(' ')[0]
            isbns.append(isbn)
    
    print(f"Found {len(isbns)} ISBNs in the file")
    
    # Check each ISBN
    invalid_count = 0
    
    for i, isbn in enumerate(isbns, 1):
        is_valid, info = check_isbn(isbn, verbose=False)
        
        if not is_valid:
            invalid_count += 1
            print(f"ISBN #{i} is INVALID: {isbn}")
            print(f"  Publisher code: {info['publisher_code']}")
            print(f"  Expected remainders: {info['expected_remainders']}")
            print(f"  Actual remainders: {info['actual_remainders']}")
    
    # Summary
    if invalid_count == 0:
        print(f"All {len(isbns)} ISBNs follow the Chinese Remainder Theorem rules!")
    else:
        print(f"Found {invalid_count} invalid ISBNs out of {len(isbns)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide the filename to check")
        print("Usage: python check_file_isbns.py filename.txt")
        sys.exit(1)
    
    check_file_isbns(sys.argv[1]) 