function submitQuestion() {
  const question = document.getElementById('search').value.trim();
  const messageContainer = document.getElementById('message-container');
  
  if (!question) {
    messageContainer.innerHTML = '<div class="error-message" style="color: red;"><p>Please enter a question</p></div>';
    return;
  }
  
  // Get CSRF token from the page
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  
  // Create FormData
  const formData = new FormData();
  formData.append('question', question);
  
  console.log('Submitting question:', question);
  
  fetch('/home/search/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken,
    },
    body: formData
  })
  .then(response => {
    console.log('Response status:', response.status);
    return response.json();
  })
  .then(data => {
    console.log('Response data:', data);
    if (data.status === 'success') {
      // Redirect to chatbot with the question
      console.log('Redirecting to chatbot');
      window.location.href = '/chatbot/?q=' + encodeURIComponent(question);
    } else {
      messageContainer.innerHTML = '<div class="error-message"><p>' + data.message + '</p></div>';
    }
  })
  .catch(error => {
    console.error('Fetch error:', error);
    messageContainer.innerHTML = '<div class="error-message"><p>An error occurred: ' + error.message + '</p></div>';
  });
}

// Allow Enter key to submit
document.getElementById('search').addEventListener('keypress', function(e) {
  if (e.key === 'Enter') {
    submitQuestion();
  }
});