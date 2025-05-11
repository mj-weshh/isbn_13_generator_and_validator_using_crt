// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Tab switching
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and panes
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));
            
            // Add active class to current button and corresponding pane
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });
    
    // Generate single ISBN
    const generateBtn = document.getElementById('generate-btn');
    generateBtn.addEventListener('click', async () => {
        const countryCode = document.getElementById('country-code').value || '3';
        const publisherCode = document.getElementById('publisher-code').value || '16';
        const useMultiples = document.getElementById('use-multiples').checked;
        
        try {
            // Show loading state
            generateBtn.textContent = 'Generating...';
            generateBtn.disabled = true;
            
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    country_code: countryCode,
                    publisher_code: publisherCode,
                    use_multiples: useMultiples
                })
            });
            
            const data = await response.json();
            
            if (data.isbn) {
                // Format ISBN with hyphens for display
                const formattedIsbn = `${data.isbn.substring(0, 3)}-${data.isbn.substring(3, 4)}-${data.isbn.substring(4, 6)}-${data.isbn.substring(6)}`;
                
                // Update result display
                document.getElementById('isbn-result').textContent = formattedIsbn;
                document.getElementById('pub-code').textContent = data.publisher_code;
                document.getElementById('book-number').textContent = data.isbn.substring(6);
                document.getElementById('status').textContent = data.valid ? 'Valid' : 'Invalid';
                document.getElementById('status').className = data.valid ? 'valid' : 'invalid';
                
                // Show result box
                document.getElementById('result').classList.remove('hidden');
            } else {
                alert('Failed to generate ISBN: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error generating ISBN:', error);
            alert('Error generating ISBN. Please try again.');
        } finally {
            // Reset button state
            generateBtn.textContent = 'Generate ISBN';
            generateBtn.disabled = false;
        }
    });
    
    // Validate ISBN
    const validateBtn = document.getElementById('validate-btn');
    validateBtn.addEventListener('click', async () => {
        const isbn = document.getElementById('isbn-input').value.trim();
        
        if (!isbn || isbn.length !== 13) {
            alert('Please enter a valid 13-digit ISBN');
            return;
        }
        
        try {
            // Show loading state
            validateBtn.textContent = 'Validating...';
            validateBtn.disabled = true;
            
            const response = await fetch('/api/validate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ isbn })
            });
            
            const data = await response.json();
            
            // Format ISBN with hyphens for display
            const formattedIsbn = `${isbn.substring(0, 3)}-${isbn.substring(3, 4)}-${isbn.substring(4, 6)}-${isbn.substring(6)}`;
            
            // Update validation display
            document.getElementById('validation-isbn').textContent = formattedIsbn;
            document.getElementById('validation-status').textContent = data.valid ? 'VALID' : 'INVALID';
            document.getElementById('validation-status').className = data.valid ? 'valid' : 'invalid';
            
            // Update remainder table
            document.getElementById('expected-r3').textContent = data.expected_remainders[0];
            document.getElementById('expected-r5').textContent = data.expected_remainders[1];
            document.getElementById('expected-r7').textContent = data.expected_remainders[2];
            document.getElementById('expected-r11').textContent = data.expected_remainders[3];
            document.getElementById('expected-r13').textContent = data.expected_remainders[4];
            
            document.getElementById('actual-r3').textContent = data.actual_remainders[0];
            document.getElementById('actual-r5').textContent = data.actual_remainders[1];
            document.getElementById('actual-r7').textContent = data.actual_remainders[2];
            document.getElementById('actual-r11').textContent = data.actual_remainders[3];
            document.getElementById('actual-r13').textContent = data.actual_remainders[4];
            
            document.getElementById('valid-r3').textContent = data.expected_remainders[0] === data.actual_remainders[0] ? '✓' : '✗';
            document.getElementById('valid-r5').textContent = data.expected_remainders[1] === data.actual_remainders[1] ? '✓' : '✗';
            document.getElementById('valid-r7').textContent = data.expected_remainders[2] === data.actual_remainders[2] ? '✓' : '✗';
            document.getElementById('valid-r11').textContent = data.expected_remainders[3] === data.actual_remainders[3] ? '✓' : '✗';
            document.getElementById('valid-r13').textContent = data.expected_remainders[4] === data.actual_remainders[4] ? '✓' : '✗';
            
            document.getElementById('valid-r3').className = data.expected_remainders[0] === data.actual_remainders[0] ? 'valid' : 'invalid';
            document.getElementById('valid-r5').className = data.expected_remainders[1] === data.actual_remainders[1] ? 'valid' : 'invalid';
            document.getElementById('valid-r7').className = data.expected_remainders[2] === data.actual_remainders[2] ? 'valid' : 'invalid';
            document.getElementById('valid-r11').className = data.expected_remainders[3] === data.actual_remainders[3] ? 'valid' : 'invalid';
            document.getElementById('valid-r13').className = data.expected_remainders[4] === data.actual_remainders[4] ? 'valid' : 'invalid';
            
            // Show result box
            document.getElementById('validation-result').classList.remove('hidden');
        } catch (error) {
            console.error('Error validating ISBN:', error);
            alert('Error validating ISBN. Please try again.');
        } finally {
            // Reset button state
            validateBtn.textContent = 'Validate ISBN';
            validateBtn.disabled = false;
        }
    });
    
    // Batch generate ISBNs
    const batchGenerateBtn = document.getElementById('batch-generate-btn');
    batchGenerateBtn.addEventListener('click', async () => {
        const countryCode = document.getElementById('batch-country-code').value || '3';
        const publisherCode = document.getElementById('batch-publisher-code').value || '16';
        const count = parseInt(document.getElementById('batch-count').value) || 10;
        const useMultiples = document.getElementById('batch-use-multiples').checked;
        
        if (count < 1 || count > 250) {
            alert('Please enter a number between 1 and 250');
            return;
        }
        
        try {
            // Show loading state
            batchGenerateBtn.textContent = 'Generating...';
            batchGenerateBtn.disabled = true;
            
            const response = await fetch('/api/batch-generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    country_code: countryCode,
                    publisher_code: publisherCode,
                    count: count,
                    use_multiples: useMultiples
                })
            });
            
            const data = await response.json();
            
            if (data.isbns && data.isbns.length > 0) {
                // Update summary
                document.getElementById('batch-summary').textContent = 
                    `Successfully generated ${data.isbns.length} ISBNs with prefix ${data.prefix}`;
                
                // Clear previous list
                const isbnList = document.getElementById('isbn-list');
                isbnList.innerHTML = '';
                
                // Add each ISBN to the list
                data.isbns.forEach((isbn, index) => {
                    const formattedIsbn = `${isbn.substring(0, 3)}-${isbn.substring(3, 4)}-${isbn.substring(4, 6)}-${isbn.substring(6)}`;
                    
                    const isbnItem = document.createElement('div');
                    isbnItem.className = 'isbn-item';
                    isbnItem.innerHTML = `
                        <span class="isbn-number">${index + 1}.</span> 
                        ${formattedIsbn}
                    `;
                    
                    isbnList.appendChild(isbnItem);
                });
                
                // Show result box
                document.getElementById('batch-result').classList.remove('hidden');
                
                // Setup download button
                setupDownloadButton(data.isbns, data.prefix);
            } else {
                alert('Failed to generate ISBNs: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error generating ISBNs:', error);
            alert('Error generating ISBNs. Please try again.');
        } finally {
            // Reset button state
            batchGenerateBtn.textContent = 'Generate ISBNs';
            batchGenerateBtn.disabled = false;
        }
    });
    
    // Setup download button for batch results
    function setupDownloadButton(isbns, prefix) {
        const downloadBtn = document.getElementById('download-btn');
        
        downloadBtn.addEventListener('click', () => {
            let content = `Generated ISBNs with prefix ${prefix}:\n\n`;
            
            isbns.forEach((isbn, index) => {
                const formattedIsbn = `${isbn.substring(0, 3)}-${isbn.substring(3, 4)}-${isbn.substring(4, 6)}-${isbn.substring(6)}`;
                content += `${index + 1}. ${isbn} (Format: ${formattedIsbn})\n`;
            });
            
            // Create a blob and download link
            const blob = new Blob([content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `isbn13_${prefix}_${isbns.length}.txt`;
            document.body.appendChild(a);
            a.click();
            
            // Cleanup
            setTimeout(() => {
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
            }, 0);
        });
    }
}); 