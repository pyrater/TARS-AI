import requests

# Define the URL of your local Ollama server
url = "http://localhost:11434/api/generate"

# Define the payload with the input text and other parameters
payload = {
    "model": "llama3.2",
    "prompt": "How are you today?",
    "stream": False
}

try:
    # Make a POST request to the local server
    response = requests.post(url, json=payload)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        result = response.json()
        
        # Debugging information
        print("Full Response:", result)
        generated_text = result.get("generated_text", "No text generated")
        print("Generated text:", generated_text)
    else:
        print(f"Request failed with status code {response.status_code}")
        print("Response:", response.text)
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")