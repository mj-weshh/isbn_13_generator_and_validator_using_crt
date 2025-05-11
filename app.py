#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template, send_from_directory
import os
import re
import json
from isbn13_crt import generate_isbn, check_isbn, isbn_storage

# Create Flask app
app = Flask(__name__, static_folder='static')

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """Generate a single ISBN"""
    data = request.json
    country_code = data.get('country_code', '3')
    publisher_code = data.get('publisher_code', '16')
    use_multiples = data.get('use_multiples', True)
    
    # Validate inputs
    if not re.match(r'^\d$', country_code):
        return jsonify({'error': 'Country code must be a single digit (0-9)'}), 400
        
    if not re.match(r'^\d{1,2}$', publisher_code):
        return jsonify({'error': 'Publisher code must be 1-2 digits (0-99)'}), 400
    
    # Format the publisher code as a two-digit string
    publisher_code = f"{int(publisher_code):02d}"
    
    # Form the prefix
    prefix = f"978{country_code}{publisher_code}"
    
    # Generate the ISBN
    isbn = generate_isbn(prefix=prefix, use_multiples=use_multiples, verbose=False)
    
    if not isbn:
        return jsonify({'error': 'Failed to generate a unique ISBN'}), 400
    
    # Check if it's valid (it should be, but verify anyway)
    is_valid, _ = check_isbn(isbn, verbose=False)
    
    return jsonify({
        'isbn': isbn,
        'valid': is_valid,
        'publisher_code': publisher_code,
        'country_code': country_code,
        'book_number': isbn[6:]
    })

@app.route('/api/validate', methods=['POST'])
def api_validate():
    """Validate an ISBN"""
    data = request.json
    isbn = data.get('isbn', '')
    
    # Validate input
    if not isbn or not re.match(r'^\d{13}$', isbn):
        return jsonify({'error': 'ISBN must be 13 digits'}), 400
    
    # Check the ISBN
    is_valid, info = check_isbn(isbn, verbose=False)
    
    # Prepare response
    response = {
        'isbn': isbn,
        'valid': is_valid,
        'publisher_code': info['publisher_code'],
        'expected_remainders': info['expected_remainders'],
        'actual_remainders': info['actual_remainders'],
        'in_storage': info.get('in_storage', False)
    }
    
    if not is_valid and 'corrected_isbn' in info:
        response['corrected_isbn'] = info['corrected_isbn']
    
    return jsonify(response)

@app.route('/api/batch-generate', methods=['POST'])
def api_batch_generate():
    """Generate multiple ISBNs with the same prefix"""
    data = request.json
    country_code = data.get('country_code', '3')
    publisher_code = data.get('publisher_code', '16')
    count = int(data.get('count', 10))
    use_multiples = data.get('use_multiples', True)
    
    # Validate inputs
    if not re.match(r'^\d$', country_code):
        return jsonify({'error': 'Country code must be a single digit (0-9)'}), 400
        
    if not re.match(r'^\d{1,2}$', publisher_code):
        return jsonify({'error': 'Publisher code must be 1-2 digits (0-99)'}), 400
    
    if count < 1 or count > 250:
        return jsonify({'error': 'Count must be between 1 and 250'}), 400
    
    # Format the publisher code as a two-digit string
    publisher_code = f"{int(publisher_code):02d}"
    
    # Form the prefix
    prefix = f"978{country_code}{publisher_code}"
    
    # Generate the ISBNs
    isbns = []
    for i in range(count):
        isbn = generate_isbn(prefix=prefix, use_multiples=use_multiples, verbose=False)
        if isbn:
            isbns.append(isbn)
        else:
            # Couldn't generate any more ISBNs
            break
    
    if not isbns:
        return jsonify({'error': 'Failed to generate any ISBNs'}), 400
    
    return jsonify({
        'isbns': isbns,
        'count': len(isbns),
        'prefix': prefix
    })

@app.route('/api/isbn-count', methods=['GET'])
def api_isbn_count():
    """Get the total number of ISBNs in storage"""
    return jsonify({
        'count': isbn_storage.count_isbns()
    })

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    # Ensure the static directory exists
    os.makedirs('static', exist_ok=True)
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000) 