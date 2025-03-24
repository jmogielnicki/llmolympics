/**
 * Shortens model names by removing the provider prefix
 */
export function shortenModelName(modelName, replacements = []) {
	// Default replacements if none provided
	if (!replacements || replacements.length === 0) {
		replacements = [
			["OpenAI ", ""],
			["Anthropic ", ""],
			["Mistral Mistral", "Mistral"],
			["xAI ", ""],
			["Google ", ""],
		];
	}

	let result = modelName;

	// Apply all replacements
	for (const [search, replace] of replacements) {
		result = result.replace(new RegExp(search, "g"), replace);
	}

	return result;
}

export function convertStarsToBold(text) {
		return text.replace(
			/\*\*(.*?)\*\*/g,
			'<strong class="font-bold">$1</strong>'
		);
	}
