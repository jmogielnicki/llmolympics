/**
 * Shortens model names by removing the provider prefix
 */
export function shortenModelName(modelName) {
	const providersToStrip = [
		"OpenAI",
		"Anthropic",
		"Mistral",
		"xAI",
		"Google",
	];

	for (const provider of providersToStrip) {
		if (modelName.startsWith(provider)) {
			return modelName.slice(provider.length + 1);
		}
	}

	return modelName;
}
