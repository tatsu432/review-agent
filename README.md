# review-agent

## Google Maps Places tool

Set the following environment variable to enable the `google_maps_places` tool:

```bash
export GOOGLE_MAPS_API_KEY="your_api_key_here"
```

The tool returns for each place:
- name
- rating
- price_level (0-4 as defined by Google)
- types
- photo_reference (use Places Photo endpoint to render; never expose API keys)
- place_url (maps link)

Example usage inside the agent: the model may call `google_maps_places` with a query such as "ramen near Shinjuku, Tokyo" and use the structured fields for presentation.