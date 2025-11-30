// api_fetch.js

// Helper function for copying text to clipboard
function copyApiText(text, event) {
    navigator.clipboard.writeText(text).then(() => {
        const button = event.target.closest('button');
        if (!button) return;

        const originalContent = button.innerHTML;
        button.innerHTML = 'Copied!';
        button.disabled = true;

        setTimeout(() => {
            button.innerHTML = originalContent;
            button.disabled = false;
        }, 1500);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}

// Helper function to create a row with a label, value, and copy button
function createDetailRow(label, value) {
    const valStr = String(value || 'N/A');
    const copyIcon = `<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>`;
    return `
        <div class="py-1">
            <strong class="text-gray-600">${label}:</strong> 
            <span class="font-mono">${valStr}</span>
            <button onclick="copyApiText('${valStr.replace(/'/g, "\\'")}', event)" class="ml-2 text-blue-600 hover:text-blue-800" title="Copy">${copyIcon}</button>
        </div>
    `;
}

fetch('http://localhost:5001/complaints')
  .then(response => response.json())
  .then(data => {
    const casesList = document.getElementById('casesList');
    if (casesList) {
      casesList.innerHTML = '';
      data.forEach((complaint, index) => {
        const container = document.createElement('div');
        container.className = 'bg-white p-4 rounded-lg border shadow-sm mb-4';

        let detailsHtml = `<h3 class="text-lg font-bold text-indigo-700 mb-2">Complaint ID: ${complaint.id}</h3>`;
        
        // Display all fields from the complaint object with labels
        detailsHtml += createDetailRow('Name', complaint.name);
        detailsHtml += createDetailRow('Father\'s Name', complaint.father_name);
        detailsHtml += createDetailRow('DOB', complaint.dob);
        detailsHtml += createDetailRow('Mobile No', complaint.mobile_no);
        detailsHtml += createDetailRow('WhatsApp No', complaint.phone_number);
        detailsHtml += createDetailRow('District', complaint.district);
        detailsHtml += createDetailRow('PIN Code', complaint.pin_code);
        detailsHtml += createDetailRow('Created At', new Date(complaint.created_at).toLocaleString());
        detailsHtml += createDetailRow('Handler', complaint.handler);
        detailsHtml += createDetailRow('Status', complaint.status);

        // Transactions are a JSON string, so we parse and display them
        const transactions = JSON.parse(complaint.transactions || '[]');
        detailsHtml += `<div class="mt-3 pt-3 border-t"><strong class="text-gray-800">Transactions (${transactions.length}):</strong></div>`;
        if (transactions.length > 0) {
            transactions.forEach((tx, i) => {
                detailsHtml += `<div class="pl-4 mt-2 border-l-2 border-gray-200">
                    <p class="font-semibold">Transaction #${i + 1}</p>
                    ${Object.entries(tx).map(([key, value]) => createDetailRow(key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()), value)).join('')}
                </div>`;
            });
        } else {
            detailsHtml += `<p class="pl-4 text-gray-500">No transactions recorded.</p>`;
        }

        // Add the raw data view, hidden by default
        container.innerHTML = `
            ${detailsHtml}
            <div class="mt-4">
                <button onclick="this.nextElementSibling.classList.toggle('hidden')" class="bg-gray-200 text-gray-800 px-3 py-1 rounded text-sm">Show/Hide Raw Data</button>
                <pre class="hidden bg-gray-800 text-white p-3 rounded border border-gray-600 text-xs mt-2 overflow-x-auto">${JSON.stringify(complaint, null, 2)}</pre>
            </div>
        `;
        casesList.appendChild(container);
      });
    }
  })
  .catch(error => console.error('Error fetching complaints:', error));
