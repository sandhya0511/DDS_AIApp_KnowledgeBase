async function postGenerate(payload) {
  const res = await fetch('/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'Request failed');
  }
  return res.json();
}

function renderTestCases(testcases) {
  let html = '';
  
  // Positive cases
  if (testcases.positive_cases && testcases.positive_cases.length) {
    html += '<h4>Positive Cases</h4><ul>';
    testcases.positive_cases.forEach(tc => {
      html += `<li><strong>${tc.id}: ${tc.title}</strong><br/>
               Preconditions: ${tc.preconditions}<br/>
               Expected: ${tc.expected_result}</li>`;
    });
    html += '</ul>';
  }
  
  // Negative cases
  if (testcases.negative_cases && testcases.negative_cases.length) {
    html += '<h4>Negative Cases</h4><ul>';
    testcases.negative_cases.forEach(tc => {
      html += `<li><strong>${tc.id}: ${tc.title}</strong><br/>
               Preconditions: ${tc.preconditions}<br/>
               Expected: ${tc.expected_result}</li>`;
    });
    html += '</ul>';
  }
  
  // Edge cases
  if (testcases.edge_cases && testcases.edge_cases.length) {
    html += '<h4>Edge Cases</h4><ul>';
    testcases.edge_cases.forEach(tc => {
      html += `<li><strong>${tc.id}: ${tc.title}</strong><br/>
               Preconditions: ${tc.preconditions}<br/>
               Expected: ${tc.expected_result}</li>`;
    });
    html += '</ul>';
  }
  
  return html || '<p>(no structured test cases)</p>';
}

document.getElementById('generate').addEventListener('click', async () => {
  const key = document.getElementById('key').value;
  const summary = document.getElementById('summary').value;
  const description = document.getElementById('description').value;
  const use_history = document.getElementById('use_history').checked;
  const mock = document.getElementById('mock').checked;

  const payload = { key, summary, description, use_history, mock, structured_json: true };

  try {
    document.getElementById('testcases').innerHTML = '<em>Generating...</em>';
    document.getElementById('selenium').textContent = '';
    document.getElementById('playwright').textContent = '';
    document.getElementById('history').innerHTML = '';
    document.getElementById('rate-limit').innerHTML = '';

    const resp = await postGenerate(payload);

    // Render structured test cases
    if (resp.testcases && Object.keys(resp.testcases).length > 0) {
      document.getElementById('testcases').innerHTML = renderTestCases(resp.testcases);
    } else {
      document.getElementById('testcases').innerHTML = '<pre>' + (resp.testcases_markdown || '(no content)') + '</pre>';
    }

    document.getElementById('selenium').textContent = resp.selenium_script || '(no script)';
    document.getElementById('playwright').textContent = resp.playwright_script || '(no script)';

    const histList = document.getElementById('history');
    if (resp.history && resp.history.length) {
      let histHtml = '';
      resp.history.forEach(h => {
        histHtml += `<li><strong>${h.file}</strong>: ${h.snippet.substring(0,150).replace(/\n/g,' ')}...</li>`;
      });
      histList.innerHTML = histHtml;
    } else {
      histList.innerHTML = '<li>(no historical matches)</li>';
    }

    // Show rate limit status
    if (resp.rate_limit_status) {
      const status = resp.rate_limit_status;
      const rateLimitDiv = document.getElementById('rate-limit');
      let rateLimitHtml = '<strong>API Usage:</strong> ';
      rateLimitHtml += `Calls: ${status.total_api_calls}, Tokens: ${status.total_tokens_used}`;
      if (status.is_rate_limited) {
        rateLimitHtml += ` ⚠️ Rate limited (resets in ${status.rate_limit_resets_in_seconds?.toFixed(1)}s)`;
      }
      rateLimitDiv.innerHTML = rateLimitHtml;
    }

  } catch (err) {
    document.getElementById('testcases').innerHTML = '<pre style="color:red">Error: ' + err.message + '</pre>';
  }
});

