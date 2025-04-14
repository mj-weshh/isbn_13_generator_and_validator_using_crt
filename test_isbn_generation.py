#!/usr/bin/env python3
import re
import sys
from isbn13_crt import generate_isbn, check_isbn

# Number of ISBNs to generate
NUM_TO_GENERATE = 100
PREFIX = "978316"

def test_isbn_generation():
    """Generate and verify multiple ISBNs with the same prefix"""
    print(f"Generating {NUM_TO_GENERATE} ISBNs with prefix {PREFIX}...")
    
    isbns = []
    for i in range(NUM_TO_GENERATE):
        # Generate a new ISBN
        new_isbn = generate_isbn(prefix=PREFIX, verbose=False)
        
        if not new_isbn:
            print(f"Failed to generate ISBN #{i+1}")
            break
            
        isbns.append(new_isbn)
        
        # Verify it satisfies CRT rules
        is_valid, info = check_isbn(new_isbn, verbose=False)
        
        if i < 10:  # Print details for just the first 10 for brevity
            print(f"ISBN #{i+1}: {new_isbn[:3]}-{new_isbn[3:4]}-{new_isbn[4:6]}-{new_isbn[6:]}")
            print(f"  Valid CRT: {is_valid}")
            print(f"  Publisher code: {info['publisher_code']}")
            print(f"  Expected remainders (mod 3,5,7): {info['expected_remainders']}")
            print(f"  Actual remainders (mod 3,5,7): {info['actual_remainders']}")
            print()
    
    all_valid = all(check_isbn(isbn, verbose=False)[0] for isbn in isbns)
    print(f"Generated {len(isbns)} ISBNs successfully.")
    print(f"All ISBNs follow CRT rules: {all_valid}")
    
    # Save to a file for verification
    if isbns:
        filename = f"isbn13_{PREFIX}_{len(isbns)}_valid.txt"
        with open(filename, 'w') as f:
            f.write(f"Generated ISBNs with prefix {PREFIX}:\n\n")
            for i, isbn in enumerate(isbns, 1):
                f.write(f"{i}. {isbn} (Format: {isbn[:3]}-{isbn[3:4]}-{isbn[4:6]}-{isbn[6:]})\n")
        print(f"Saved all ISBNs to {filename}")

if __name__ == "__main__":
    test_isbn_generation() 