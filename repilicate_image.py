def generate_image(prompt, index):
    client = replicate.Client(api_token=REPLICATE_API_TOKEN)

    output = client.run(
        "black-forest-labs/flux-schnell",
        input={
            "prompt": prompt,
            "aspect_ratio": "9:16"
        }
    )

    image_url = output[0]

    response = requests.get(image_url)
    file_path = f"scene_{index}.png"

    with open(file_path, "wb") as f:
        f.write(response.content)

    return file_path
