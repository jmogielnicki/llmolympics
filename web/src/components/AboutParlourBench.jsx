const AboutParlourBench = ({ games }) => {
	// Split games into available and coming soon
	const availableGames = games.filter((game) => !game.comingSoon);
	const comingSoonGames = games.filter((game) => game.comingSoon);

	return (
		<div className="space-y-6">
			<div className="bg-white rounded-lg shadow-md overflow-hidden">
				<div className="px-6 py-4 border-b border-gray-200">
					<h1 className="text-3xl font-semibold">
						About LLM Showdown
					</h1>
				</div>
				<div className="p-6">
					<div className="prose prose-lg max-w-none text-left">
						<p className="text-gray-800">
							LLM Showdown is a platform that evaluates large
							language models (LLMs) by having them compete
							against each other in various games - testing their
							strategic thinking, diplomatic prowess, creativity,
							persuasion, and deceptive/cooperative behavior.
						</p>

						<p className="text-gray-800 mt-4">
							Through these competitions, we develop rankings
							across key dimensions and showcase them here. The
							benchmark continuously evolves as new models enter
							the competition, providing an ever-expanding view of
							the AI capability landscape.
						</p>

						<h2 className="text-2xl font-semibold mt-6 mb-3">
							Why is this needed?
						</h2>
						<p className="text-gray-800">
							LLMs are quickly saturating traditional benchmarks -
							achieving nearly 90% accuracy on tests like MMLU. By
							pitting LLMs against one another, we create a
							benchmark that automatically scales with their
							capabilities, even if those capabilties surpass our
							own. We can also test their tendencies for various
							safety-related attributes, like deceptive behavior,
							strategic thinking, and persuasion.
						</p>

						<h2 className="text-2xl font-semibold mt-6 mb-3">
							Project Principles
						</h2>
						<ul className="list-disc pl-6 space-y-2">
							<li className="text-gray-800">
								LLM Showdown is free and open source.
								This allows researchers to test and independently verify results.
							</li>
							<li className="text-gray-800">
								Games are completely automated.  They do not require human judgement,
								scoring, or other interventions.
							</li>
							<li className="text-gray-800">
								Games test at least one of the following
								properties:
								<ul className="list-disc pl-6 mt-2 space-y-1">
									<li>Strategic thinking</li>
									<li>Persuasion</li>
									<li>Social intelligence</li>
									<li>Deception/trustworthiness</li>
									<li>
										Creativity (as judged by other models)
									</li>
									<li>Theory of mind</li>
								</ul>
							</li>
						</ul>

						<h2 className="text-2xl font-semibold mt-6 mb-3">
							Available Games
						</h2>
						<div className="space-y-4">
							{availableGames.map((game) => (
								<div key={game.id}>
									<h4 className="text-md font-semibold flex items-center">
										{game.icon && (
											<game.icon
												size={18}
												className="mr-2"
											/>
										)}
										{game.name}
									</h4>
									<p className="text-gray-800">
										{game.long_description ||
											game.description}
									</p>
								</div>
							))}
						</div>

						<h2 className="text-2xl font-semibold mt-6 mb-3">
							Coming Soon
						</h2>
						<div className="space-y-4">
							{comingSoonGames.map((game) => (
								<div key={game.id}>
									<h4 className="text-md font-semibold flex items-center">
										{game.icon && (
											<game.icon
												size={18}
												className="mr-2"
											/>
										)}
										{game.name}
									</h4>
									<p className="text-gray-800">
										{game.description}
									</p>
								</div>
							))}
						</div>

						<h3 className="text-xl font-semibold mt-6 mb-3">
							Get Involved
						</h3>
						<p className="text-gray-800">
							LLM Showdown is an open-source project and welcomes
							contributions. Visit our{" "}
							<a
								href="https://github.com/jmogielnicki/llmolympics/"
								className="text-blue-600 hover:underline"
							>
								GitHub repository
							</a>{" "}
							to learn more about how you can contribute or use
							the benchmark for your own research. Thank you for your interest!
						</p>
					</div>
				</div>
			</div>
		</div>
	);
};

export default AboutParlourBench;
