#!/usr/bin/env python3

def check_isbn_crt(isbn):
    """Check if ISBN follows the Chinese Remainder Theorem conditions"""
    # Extract publisher code (positions 4-5)
    publisher_code = int(isbn[4:6])
    full_num = int(isbn)
    
    # Calculate remainders for publisher code
    pub_r3 = publisher_code % 3
    pub_r5 = publisher_code % 5
    pub_r7 = publisher_code % 7
    
    # Calculate remainders for full ISBN
    isbn_r3 = full_num % 3
    isbn_r5 = full_num % 5
    isbn_r7 = full_num % 7
    
    # Check if the remainders match
    is_valid = (pub_r3 == isbn_r3 and pub_r5 == isbn_r5 and pub_r7 == isbn_r7)
    
    return {
        'isbn': isbn,
        'publisher_code': publisher_code,
        'pub_remainders': [pub_r3, pub_r5, pub_r7],
        'isbn_remainders': [isbn_r3, isbn_r5, isbn_r7],
        'is_valid': is_valid
    }

# Read ISBNs from the file
with open('isbn13_978316_100.txt', 'r') as f:
    lines = f.readlines()

isbns = []
for line in lines:
    # Extract ISBN from lines like "1. 9783160002016 (Format: 978-3-16-0002016)"
    if line.strip() and line[0].isdigit() and '. 978' in line:
        isbn = line.split('. ')[1].split(' ')[0]
        isbns.append(isbn)

# Check each ISBN
invalid_count = 0
for i, isbn in enumerate(isbns, 1):
    result = check_isbn_crt(isbn)
    
    if not result['is_valid']:
        invalid_count += 1
        print(f"ISBN #{i} is INVALID: {isbn}")
        print(f"  Publisher code: {result['publisher_code']}")
        print(f"  Publisher remainders (mod 3,5,7): {result['pub_remainders']}")
        print(f"  ISBN remainders (mod 3,5,7): {result['isbn_remainders']}")
        print()

# Print summary
if invalid_count == 0:
    print(f"All {len(isbns)} ISBNs follow the Chinese Remainder Theorem rules.")
else:
    print(f"Found {invalid_count} ISBNs out of {len(isbns)} that DO NOT follow CRT rules.") 