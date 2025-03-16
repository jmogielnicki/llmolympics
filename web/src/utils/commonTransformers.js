// commonTransformers.js
export const shortenModelName = (modelName) => {
	const words_to_remove = ["OpenAI", "Anthropic", "Mistral", "xAI", "Google"];
	for (let word of words_to_remove) {
		if (modelName.startsWith(word)) {
			const shortenedName = modelName.slice(word.length + 1);
			return shortenedName;
		}
	}
	return modelName;
};
