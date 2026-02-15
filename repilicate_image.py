import os
import replicate

def generate_image(prompt, index):
    client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))

    output = client.run(
        "stability-ai/sdxl:latest",
        input={
            "prompt": prompt,
            "width": 768,
            "height": 1024
        }
    )

    image_url = output[0]

    import requests
    response = requests.get(image_url)
    file_path = f"scene_{index}.png"

    with open(file_path, "wb") as f:
        f.write(response.content)

    return file_path
