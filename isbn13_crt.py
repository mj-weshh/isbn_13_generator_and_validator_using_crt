#!/usr/bin/env python3
import os
import sys
import json
import re

# File to store generated ISBNs
ISBN_STORAGE_FILE = "generated_isbns.json"

class ISBNStorage:
    """
    Class to handle storage and retrieval of generated ISBNs.
    Ensures that no ISBN is generated twice.
    """
    def __init__(self, storage_file=ISBN_STORAGE_FILE):
        self.storage_file = storage_file
        self.data = self._load_data()
    
    def _load_data(self):
        """Load previously generated ISBNs and metadata from storage file."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    # Ensure the data structure has the expected format
                    if 'isbns' not in data:
                        data = {
                            'isbns': data,  # Convert old format to new format
                            'prefix_offsets': {}
                        }
                    return data
            except json.JSONDecodeError:
                print(f"Warning: Could not parse {self.storage_file}. Starting with empty storage.")
                return {'isbns': {}, 'prefix_offsets': {}}
        return {'isbns': {}, 'prefix_offsets': {}}
    
    def _save_data(self):
        """Save the current set of ISBNs and metadata to the storage file."""
        with open(self.storage_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def add_isbn(self, publisher_code, isbn, prefix, offset):
        """
        Add a newly generated ISBN to storage and update offset tracking.
        
        Parameters:
        - publisher_code: The publisher code associated with the ISBN
        - isbn: The full 13-digit ISBN
        - prefix: The prefix used to generate the ISBN
        - offset: The offset used to generate the ISBN
        """
        # Add ISBN to the publisher code's list
        publisher_code = str(publisher_code)
        if publisher_code not in self.data['isbns']:
            self.data['isbns'][publisher_code] = []
        
        self.data['isbns'][publisher_code].append(isbn)
        
        # Update the last used offset for this prefix
        self.data['prefix_offsets'][prefix] = offset
        
        self._save_data()
    
    def get_next_offset(self, prefix):
        """
        Get the next offset to try for a specific prefix.
        
        Parameters:
        - prefix: The ISBN prefix (first 6 digits)
        
        Returns:
        - The next offset to try (one more than the last used offset, or 0 if no ISBN has been generated for this prefix)
        """
        current_offset = self.data['prefix_offsets'].get(prefix, -1)
        return (current_offset + 1) % 105  # Wrap around if we reach the maximum offset
    
    def is_isbn_generated(self, isbn):
        """
        Check if an ISBN has already been generated.
        
        Parameters:
        - isbn: The ISBN to check
        
        Returns:
        - True if the ISBN exists in storage, False otherwise
        """
        for publisher_isbns in self.data['isbns'].values():
            if isbn in publisher_isbns:
                return True
        return False
    
    def list_isbns_for_publisher(self, publisher_code):
        """
        List all ISBNs generated for a specific publisher code.
        
        Parameters:
        - publisher_code: The publisher code to check
        
        Returns:
        - List of ISBNs for the given publisher code
        """
        publisher_code = str(publisher_code)
        return self.data['isbns'].get(publisher_code, [])
    
    def count_isbns(self):
        """Return the total number of generated ISBNs."""
        count = 0
        for publisher_isbns in self.data['isbns'].values():
            count += len(publisher_isbns)
        return count
    
    @property
    def isbns(self):
        """Getter for the isbns dictionary for backward compatibility."""
        return self.data['isbns']

    def get_last_book_number(self, prefix):
        """
        Get the book number (last 7 digits) of the last ISBN generated with this prefix.
        
        Parameters:
        - prefix: The ISBN prefix (first 6 digits)
        
        Returns:
        - The book number (last 7 digits) as an integer, or None if no ISBN has been generated for this prefix
        """
        publisher_code = str(int(prefix[4:6]))
        if publisher_code not in self.data['isbns'] or not self.data['isbns'][publisher_code]:
            return None
            
        # Find ISBNs with this prefix
        for isbn in self.data['isbns'][publisher_code]:
            if isbn.startswith(prefix):
                # Extract the book number (last 7 digits)
                return int(isbn[6:])
                
        return None

# Initialize the ISBN storage
isbn_storage = ISBNStorage()

def extended_gcd(a, b):
    """
    Extended Euclidean Algorithm to find GCD and Bézout coefficients.
    Returns (gcd, x, y) such that a*x + b*y = gcd.
    """
    if a == 0:
        return b, 0, 1
    else:
        gcd, x1, y1 = extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return gcd, x, y

def mod_inverse(a, m):
    """
    Compute the modular multiplicative inverse of 'a' modulo 'm'.
    Returns x such that (a * x) % m == 1.
    """
    gcd, x, y = extended_gcd(a, m)
    if gcd != 1:
        raise ValueError(f"Modular inverse does not exist for {a} mod {m}")
    else:
        return x % m

def chinese_remainder_theorem(remainders, moduli):
    """
    Solve the system of congruences using the Chinese Remainder Theorem.
    
    Input:
    - remainders: list of remainders [r1, r2, ..., rk]
    - moduli: list of moduli [m1, m2, ..., mk]
    
    Returns the smallest positive solution to the system of congruences:
    x ≡ r1 (mod m1)
    x ≡ r2 (mod m2)
    ...
    x ≡ rk (mod mk)
    """
    # Compute the product of all moduli
    M = 1
    for m in moduli:
        M *= m
    
    # Compute the solution
    result = 0
    for i in range(len(remainders)):
        Mi = M // moduli[i]  # M divided by mi
        inv = mod_inverse(Mi, moduli[i])  # Modular inverse of Mi modulo mi
        result += remainders[i] * Mi * inv
    
    return result % M

def generate_isbn(prefix="978316", offset=None, max_attempts=105, verbose=True, use_multiples=True):
    """
    Generate a 13-digit ISBN using the Chinese Remainder Theorem.
    
    Parameters:
    - prefix: The 6-digit prefix (default: "978316")
    - offset: An offset to generate different ISBNs for the same publisher code
              If None, the next available offset from storage will be used
    - max_attempts: Maximum number of attempts to generate a unique ISBN
    - verbose: Whether to print detailed output
    - use_multiples: Whether to use multiples of the last book number (if available)
    
    Returns the generated 13-digit ISBN as a string, or None if no unique ISBN can be generated.
    """
    # Extract the publisher code from the prefix
    X = int(prefix[4:6])
    
    # Check if we should use multiples of previous book numbers
    last_book_number = None
    if use_multiples:
        last_book_number = isbn_storage.get_last_book_number(prefix)
        
    if last_book_number is not None:
        # We have a previous book number, generate a multiple
        if verbose:
            print(f"Using multiple method with previous book number...")
        
        # Start with the last book number and try multiples
        modulus = 3 * 5 * 7  # = 105
        
        # Compute remainders of X (publisher code)
        r3 = X % 3
        r5 = X % 5
        r7 = X % 7
        
        # Try different multiples
        for multiplier in range(2, max_attempts + 2):  # Start from 2 since 1 would be the same book number
            # Calculate the new book number
            new_book_number = (last_book_number * multiplier) % 10000000  # Keep within 7 digits
            
            # Form the complete ISBN
            isbn = f"{prefix}{new_book_number:07d}"
            
            # Check if this ISBN already exists
            if isbn_storage.is_isbn_generated(isbn):
                continue
            
            # Check if this ISBN satisfies the CRT conditions
            full_num = int(isbn)
            isbn_r3 = full_num % 3
            isbn_r5 = full_num % 5
            isbn_r7 = full_num % 7
            
            if isbn_r3 == r3 and isbn_r5 == r5 and isbn_r7 == r7:
                if verbose:
                    print(f"Created a new ISBN using multiple: {multiplier}")
                
                # Store the ISBN
                isbn_storage.add_isbn(X, isbn, prefix, (offset or 0))
                return isbn
        
        if verbose:
            print("Could not find a valid multiple, using alternative method...")
    
    # If no previous book number or couldn't find valid multiple, fall back to offset method
    # If no offset is provided, get the next one from storage
    if offset is None:
        offset = isbn_storage.get_next_offset(prefix)
    
    # Compute remainders of X
    r3 = X % 3
    r5 = X % 5
    r7 = X % 7
    
    # The moduli product
    modulus = 3 * 5 * 7  # = 105
    
    # Track which offsets we've already tried
    tried_offsets = set()
    
    attempts = 0
    while attempts < max_attempts and len(tried_offsets) < modulus:
        # Skip if we've already tried this offset
        if offset in tried_offsets:
            offset = (offset + 1) % modulus
            continue
        
        tried_offsets.add(offset)
        
        # Use CRT directly to solve for B
        # For a number N = prefix * 10^7 + B, we want:
        # N % 3 = X % 3
        # N % 5 = X % 5
        # N % 7 = X % 7
        
        # Target remainders and moduli
        target_remainders = [r3, r5, r7]
        moduli = [3, 5, 7]
        
        # Find B such that (prefix_int * 10^7 + B) mod m_i = r_i for all i
        prefix_int = int(prefix)
        prefix_shift = prefix_int * 10**7  # This is the value of the prefix shifted 7 places
        
        # For each modulus, find the remainder of prefix_shift
        prefix_remainders = [prefix_shift % m for m in moduli]
        
        # Calculate the needed remainders for B
        needed_remainders = [(target_remainders[i] - prefix_remainders[i]) % moduli[i] for i in range(len(moduli))]
        
        # Use CRT to find B
        B = chinese_remainder_theorem(needed_remainders, moduli)
        
        # Apply offset (adjusting B by offset * modulus)
        B = (B + offset * modulus) % 10000000  # Keep B within 7 digits
        
        # Form the complete ISBN
        isbn = f"{prefix}{B:07d}"
        
        # Check if this ISBN has already been generated
        if not isbn_storage.is_isbn_generated(isbn):
            # Verify the ISBN satisfies CRT conditions
            full_num = int(isbn)
            isbn_r3 = full_num % 3
            isbn_r5 = full_num % 5
            isbn_r7 = full_num % 7
            
            if isbn_r3 == r3 and isbn_r5 == r5 and isbn_r7 == r7:
                # Store the ISBN and the offset used
                isbn_storage.add_isbn(X, isbn, prefix, offset)
                return isbn
        
        offset = (offset + 1) % modulus
        attempts += 1
    
    if verbose:
        if len(tried_offsets) >= modulus:
            print(f"No more unique ISBNs can be generated with this prefix.")
        else:
            print(f"Failed to generate a unique ISBN.")
    return None

def check_isbn(isbn, verbose=True):
    """
    Check if an ISBN was generated using the CRT method.
    
    Parameters:
    - isbn: A string or integer representing a 13-digit ISBN
    - verbose: Whether to print detailed output
    
    Returns:
    - True if the ISBN is valid, False otherwise
    - A dictionary with additional information about the check
    """
    result_info = {
        "valid": False,
        "in_storage": False,
        "publisher_code": "",
        "expected_remainders": [],
        "actual_remainders": [],
        "corrected_isbn": "",
        "error_message": ""
    }
    
    try:
        # Convert to string if an integer is provided
        isbn_str = str(isbn)
        
        # Ensure it's a 13-digit ISBN
        if len(isbn_str) != 13:
            result_info["error_message"] = "ISBN must be 13 digits."
            if verbose:
                print("Error: ISBN must be 13 digits.")
            return False, result_info
        
        # Extract the publisher code Z from positions 5 and 6 (0-indexed: 4 and 5)
        Z = int(isbn_str[4:6])
        result_info["publisher_code"] = Z
        
        if verbose:
            print(f"Publisher code: {Z}")
        
        # Compute remainders of Z (publisher code)
        z_r3 = Z % 3
        z_r5 = Z % 5
        z_r7 = Z % 7
        result_info["expected_remainders"] = [z_r3, z_r5, z_r7]
        
        # Convert the full ISBN to an integer
        Y = int(isbn_str)
        
        # Compute the remainders of the full ISBN
        y_r3 = Y % 3
        y_r5 = Y % 5
        y_r7 = Y % 7
        result_info["actual_remainders"] = [y_r3, y_r5, y_r7]
        
        # Check if the remainders match
        if y_r3 == z_r3 and y_r5 == z_r5 and y_r7 == z_r7:
            result_info["valid"] = True
            
            if verbose:
                print(f"ISBN {isbn_str} is valid according to the CRT method.")
            
            # Check if this ISBN is in our storage
            if isbn_storage.is_isbn_generated(isbn_str):
                result_info["in_storage"] = True
                if verbose:
                    print("This ISBN has been previously generated and is in storage.")
            elif verbose:
                print("This ISBN is valid but is not in storage (not previously generated).")
                
            return True, result_info
        else:
            if verbose:
                print(f"Error: ISBN {isbn_str} is not valid according to the CRT method.")
            
            # Let's generate the correct ISBN for this publisher code
            prefix = isbn_str[:6]  # Keep the original prefix including publisher code
            prefix_int = int(prefix)
            
            # Target remainders from the publisher code
            target_remainders = [z_r3, z_r5, z_r7]
            moduli = [3, 5, 7]
            
            # For each modulus, find the remainder of prefix_shift
            prefix_shift = prefix_int * 10**7
            prefix_remainders = [prefix_shift % m for m in moduli]
            
            # Calculate the needed remainders for B
            needed_remainders = [(target_remainders[i] - prefix_remainders[i]) % moduli[i] for i in range(len(moduli))]
            
            # Use CRT to find B
            B = chinese_remainder_theorem(needed_remainders, moduli)
            
            # Make sure B is in the range [0, 10^7 - 1]
            while B >= 10**7:
                B -= 3 * 5 * 7
            
            # If B is negative, add modulus until it's positive
            while B < 0:
                B += 3 * 5 * 7
            
            # Form the correct ISBN
            correct_isbn = f"{prefix}{B:07d}"
            result_info["corrected_isbn"] = correct_isbn
            
            if verbose:
                print(f"A valid ISBN with this prefix would be: {correct_isbn}")
            
            return False, result_info
    
    except ValueError as e:
        result_info["error_message"] = f"Invalid ISBN format - {e}"
        if verbose:
            print(f"Error: Invalid ISBN format - {e}")
        return False, result_info

def generate_isbn_with_publisher_code(publisher_code, offset=None, max_attempts=105, verbose=True):
    """
    Generate a 13-digit ISBN using the Chinese Remainder Theorem 
    with a custom publisher code.
    
    Parameters:
    - publisher_code: A two-digit string or integer publisher code
    - offset: An offset to generate different ISBNs for the same publisher code
    - max_attempts: Maximum number of attempts to generate a unique ISBN
    - verbose: Whether to print detailed output
    
    Returns the generated 13-digit ISBN as a string, or None if no unique ISBN can be generated.
    """
    try:
        # Convert to integer if a string is provided
        X = int(publisher_code)
        
        # Ensure it's a two-digit number
        if X < 0 or X > 99:
            if verbose:
                print(f"Error: Publisher code must be a two-digit number (0-99)")
            return None
            
        # Fixed part of the prefix
        prefix = "9783"
        
        # Format the publisher code as a two-digit string
        formatted_publisher = f"{X:02d}"
        
        # Full prefix including publisher code
        full_prefix = f"{prefix}{formatted_publisher}"
        
        return generate_isbn(prefix=full_prefix, offset=offset, max_attempts=max_attempts, verbose=verbose)
        
    except ValueError as e:
        if verbose:
            print(f"Error: {e}")
        return None

def list_stored_isbns():
    """
    List all ISBNs that have been generated and stored.
    """
    print("\n=== Generated ISBNs in Storage ===")
    print("--------------------------------------------------")
    
    if isbn_storage.count_isbns() == 0:
        print("No ISBNs have been generated yet.")
        print("--------------------------------------------------")
        return
    
    # Display ISBNs organized by publisher code
    for publisher_code, isbns in isbn_storage.isbns.items():
        print(f"\nPublisher code {publisher_code} ({len(isbns)} ISBNs):")
        for i, isbn in enumerate(isbns, 1):
            # Format with hyphens for better readability
            formatted_isbn = f"{isbn[:3]}-{isbn[3:4]}-{isbn[4:6]}-{isbn[6:]}"
            print(f"  {i}. {formatted_isbn}")
    
    print(f"\nTotal ISBNs in storage: {isbn_storage.count_isbns()}")
    print("--------------------------------------------------")

def generate_multiple_isbns():
    """
    Generate multiple ISBNs with the same prefix.
    """
    print("\n=== Generate Multiple ISBNs ===")
    print("This will generate multiple ISBN-13 codes with the same prefix.")
    
    # Get country code (1 digit)
    country_code = get_valid_input(
        "Enter the country code (1 digit)",
        r"^\d$",
        "The country code must be a single digit (0-9)."
    )
    
    # Get publisher code (2 digits)
    publisher_code = get_valid_input(
        "Enter the publisher code (2 digits)",
        r"^\d{2}$",
        "The publisher code must be two digits (00-99)."
    )
    
    # Get the number of ISBNs to generate
    count = get_valid_input(
        "Enter the number of ISBNs to generate (1-100)",
        r"^([1-9]|[1-9][0-9]|100)$",
        "Please enter a number between 1 and 100."
    )
    count = int(count)
    
    # Form the prefix
    prefix = f"978{country_code}{publisher_code}"
    
    # Ask if user wants to use multiples
    use_multiples = get_valid_input(
        "Generate ISBNs using multiples of book numbers? (y/n)",
        r"^[yn]$",
        "Please enter 'y' or 'n'."
    ) == 'y'
    
    print(f"\nGenerating {count} ISBNs with prefix: {prefix}")
    print("--------------------------------------------------")
    
    # Generate the ISBNs
    generated_isbns = []
    for i in range(count):
        print(f"\nGenerating ISBN #{i+1}...")
        new_isbn = generate_isbn(prefix=prefix, use_multiples=use_multiples, verbose=False)
        
        if new_isbn:
            generated_isbns.append(new_isbn)
            print(f"ISBN: {new_isbn[:3]}-{new_isbn[3:4]}-{new_isbn[4:6]}-{new_isbn[6:]}")
        else:
            print(f"Failed to generate ISBN #{i+1}.")
            print("No more unique ISBNs can be generated for this prefix.")
            break
    
    print("\n--------------------------------------------------")
    print(f"Successfully generated {len(generated_isbns)} ISBNs with prefix {prefix}.")
    
    # Option to save to a file
    if len(generated_isbns) > 0:
        save_option = get_valid_input(
            "Would you like to save these ISBNs to a separate text file? (y/n)",
            r"^[yn]$",
            "Please enter 'y' or 'n'."
        )
        
        if save_option == 'y':
            filename = f"isbn13_{prefix}_{len(generated_isbns)}.txt"
            with open(filename, 'w') as f:
                f.write(f"Generated ISBNs with prefix {prefix}:\n\n")
                for i, isbn in enumerate(generated_isbns, 1):
                    f.write(f"{i}. {isbn} (Format: {isbn[:3]}-{isbn[3:4]}-{isbn[4:6]}-{isbn[6:]})\n")
            print(f"ISBNs saved to {filename}")

def get_valid_input(prompt, pattern, error_message, default=None):
    """
    Get and validate user input.
    
    Parameters:
    - prompt: The prompt to display to the user
    - pattern: Regular expression pattern to validate input
    - error_message: Message to display if validation fails
    - default: Default value if user enters nothing
    
    Returns the validated input.
    """
    while True:
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            if not user_input:
                return default
        else:
            user_input = input(f"{prompt}: ").strip()
            
        if not user_input and not default:
            continue
            
        if re.match(pattern, user_input):
            return user_input
        else:
            print(error_message)

def interactive_isbn_generation():
    """
    Guide the user through generating a new ISBN.
    """
    print("\n=== ISBN-13 Generation ===")
    print("ISBN-13 Structure:")
    print("- First 3 digits: '978' (fixed GS1 prefix)")
    print("- Next 1 digit: Country code")
    print("- Next 2 digits: Unique publisher code")
    print("- Last 7 digits: Book number (generated using CRT)")
    
    # Get country code (1 digit)
    country_code = get_valid_input(
        "Enter the country code (1 digit)",
        r"^\d$",
        "The country code must be a single digit (0-9)."
    )
    
    # Get publisher code (2 digits)
    publisher_code = get_valid_input(
        "Enter the publisher code (2 digits)",
        r"^\d{2}$",
        "The publisher code must be two digits (00-99)."
    )
    
    # Form the prefix
    prefix = f"978{country_code}{publisher_code}"
    
    # Ask if user wants to use multiples if previous ISBNs exist
    use_multiples = False
    if isbn_storage.get_last_book_number(prefix) is not None:
        use_multiples = get_valid_input(
            "Generate ISBN using multiple of previous book number? (y/n)",
            r"^[yn]$",
            "Please enter 'y' or 'n'."
        ) == 'y'
    
    print(f"\nGenerating ISBN with prefix: {prefix}")
    print("--------------------------------------------------")
    
    # Generate the ISBN
    new_isbn = generate_isbn(prefix=prefix, use_multiples=use_multiples, verbose=False)
    
    if new_isbn:
        print(f"Generated ISBN: {new_isbn}")
        print(f"Format: {new_isbn[:3]}-{new_isbn[3:4]}-{new_isbn[4:6]}-{new_isbn[6:]}")
        
        # Validate the ISBN
        is_valid, info = check_isbn(new_isbn, verbose=False)
        print("Status: Valid ISBN (satisfies CRT conditions)")
    else:
        print("\nFailed to generate a unique ISBN. Please try with a different publisher code.")
    
    print("--------------------------------------------------")

def interactive_isbn_validation():
    """
    Guide the user through validating an existing ISBN.
    """
    print("\n=== ISBN-13 Validation ===")
    print("ISBN-13 Structure:")
    print("- First 3 digits: '978' (fixed GS1 prefix)")
    print("- Next 1 digit: Country code")
    print("- Next 2 digits: Unique publisher code")
    print("- Last 7 digits: Book number (generated using CRT)")
    
    # Option 1: Enter the full ISBN
    print("\nOption 1: Enter the full 13-digit ISBN")
    
    # Option 2: Enter it section by section
    print("Option 2: Enter the ISBN section by section")
    
    choice = get_valid_input(
        "Choose an option (1 or 2)",
        r"^[12]$",
        "Please enter either 1 or 2."
    )
    
    if choice == "1":
        # Get the full ISBN
        isbn = get_valid_input(
            "Enter the full 13-digit ISBN (digits only, no hyphens)",
            r"^\d{13}$",
            "The ISBN must consist of exactly 13 digits."
        )
    else:
        # Get the ISBN section by section
        print("\nEntering ISBN section by section:")
        
        # GS1 prefix (always 978 for books)
        gs1_prefix = get_valid_input(
            "Enter the GS1 prefix (3 digits)",
            r"^\d{3}$",
            "The GS1 prefix must be three digits.",
            "978"
        )
        
        # Country code (1 digit)
        country_code = get_valid_input(
            "Enter the country code (1 digit)",
            r"^\d$",
            "The country code must be a single digit (0-9)."
        )
        
        # Publisher code (2 digits)
        publisher_code = get_valid_input(
            "Enter the publisher code (2 digits)",
            r"^\d{2}$",
            "The publisher code must be two digits (00-99)."
        )
        
        # Book number (7 digits)
        book_number = get_valid_input(
            "Enter the book number (7 digits)",
            r"^\d{7}$",
            "The book number must be seven digits."
        )
        
        # Combine the parts
        isbn = f"{gs1_prefix}{country_code}{publisher_code}{book_number}"
    
    # Display the ISBN with hyphens for clarity
    print(f"\nValidating ISBN: {isbn[:3]}-{isbn[3:4]}-{isbn[4:6]}-{isbn[6:]}")
    print("--------------------------------------------------")
    
    # Validate the ISBN
    is_valid, info = check_isbn(isbn, verbose=False)
    
    if is_valid:
        print("Result: VALID")
        print("This ISBN satisfies the CRT criteria.")
        
        if info["in_storage"]:
            print("This ISBN has been previously generated and is in storage.")
        else:
            print("This ISBN is valid but is not in our database.")
    else:
        print("Result: INVALID")
        print("This ISBN does not satisfy the CRT criteria.")
        
        if info["corrected_isbn"]:
            corrected_isbn = info["corrected_isbn"]
            print(f"\nA valid ISBN with this prefix would be: {corrected_isbn}")
            print(f"Format: {corrected_isbn[:3]}-{corrected_isbn[3:4]}-{corrected_isbn[4:6]}-{corrected_isbn[6:]}")
    
    print("--------------------------------------------------")

def main_menu():
    """
    Display and handle the main menu.
    """
    print("\n============================================")
    print("  ISBN-13 CRT Generator and Validator")
    print("============================================")
    print("This program implements ISBN-13 codes using")
    print("the Chinese Remainder Theorem (CRT)")
    print(f"[Database: {isbn_storage.count_isbns()} ISBNs in storage]")
    
    while True:
        print("\nMenu Options:")
        print("  1. Generate a single ISBN-13")
        print("  2. Generate multiple ISBN-13s with the same prefix")
        print("  3. Validate an existing ISBN-13")
        print("  4. List all stored ISBNs")
        print("  5. Exit")
        
        choice = get_valid_input(
            "Enter your choice (1-5)",
            r"^[1-5]$",
            "Please enter a number between 1 and 5."
        )
        
        if choice == "1":
            interactive_isbn_generation()
        elif choice == "2":
            generate_multiple_isbns()
        elif choice == "3":
            interactive_isbn_validation()
        elif choice == "4":
            list_stored_isbns()
        else:
            print("\nExiting the ISBN-13 generator. Goodbye!")
            break

if __name__ == "__main__":
    """
    Main function to run the interactive ISBN-13 generator and validator.
    """
    # Check if we should run the automated tests or the interactive mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # For automated testing and demonstration
        print("=== ISBN-13 CRT Generator and Validator (Test Mode) ===\n")
        
        # Display the number of previously generated ISBNs
        print(f"Found {isbn_storage.count_isbns()} previously generated ISBNs in storage.")
        
        # Test generating multiple ISBNs with the same prefix
        prefix = "978316"
        num_to_generate = 10
        print(f"\nGenerating {num_to_generate} unique ISBNs with prefix {prefix}...")
        
        for i in range(num_to_generate):
            print(f"\nGenerating ISBN #{i+1}:")
            new_isbn = generate_isbn(prefix=prefix)
            if new_isbn:
                print(f"Generated ISBN: {new_isbn}")
                sys.stdout.flush()
            else:
                print(f"Failed to generate ISBN #{i+1}.")
                break
        
        # List all stored ISBNs
        list_stored_isbns()
        
        print("\nTest mode completed successfully.")
    else:
        # Run the interactive mode
        main_menu() 