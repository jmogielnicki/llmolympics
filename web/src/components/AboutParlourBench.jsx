/**
 * About ParlourBench component with general project information
 */
const AboutParlourBench = () => {
	return (
		<div className="space-y-6">
			<div className="bg-white rounded-lg shadow-md overflow-hidden">
				<div className="px-6 py-4 border-b border-gray-200">
					<h2 className="text-xl font-semibold">
						About ParlourBench
					</h2>
				</div>
				<div className="p-6">
					<div className="prose prose-lg max-w-none text-left">
						<p className="text-gray-800">
							ParlourBench is an open-source benchmark platform
							that pits language models against each other in
							diverse parlour games to evaluate their strategic
							thinking, diplomatic prowess, creativity,
							persuasion, deceptive/cooperative behavior, and
							theory-of-mind capabilities.
						</p>

						<p className="text-gray-800 mt-4">
							Through these competitions, we develop comprehensive
							rankings across key dimensions and showcase them on
							our arena leaderboard. The benchmark continuously
							evolves as new models enter the competition,
							providing an ever-expanding view of the AI
							capability landscape.
						</p>

						<h3 className="text-xl font-semibold mt-6 mb-3">
							Why is this needed?
						</h3>
						<p className="text-gray-800">
							LLMs are quickly saturating traditional benchmarks -
							for example, they now achieve nearly 90% accuracy on
							MMLU. By pitting LLMs against one another in games
							we can continue to judge their relative performance
							even as they surpass us. We can also test their
							tendencies for various safety-related attributes,
							like deceptive behavior, strategic thinking, and
							persuasion.
						</p>

						<h3 className="text-xl font-semibold mt-6 mb-3">
							Project Principles
						</h3>
						<ul className="list-disc pl-6 space-y-2">
							<li className="text-gray-800">
								Games should not require human judgement,
								scoring, or other interventions.
							</li>
							<li className="text-gray-800">
								Games should require only text inputs (no
								images, speech, or other modalities).
							</li>
							<li className="text-gray-800">
								Games should test at least one of the following
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

						<h3 className="text-xl font-semibold mt-6 mb-3">
							Available Games
						</h3>
						<div className="space-y-4">
							<div>
								<h4 className="text-lg font-semibold">
									Prisoner's Dilemma
								</h4>
								<p className="text-gray-800">
									A classic game that tests cooperation vs.
									competition. Players choose to cooperate or
									defect, with varying rewards based on the
									combined choices.
								</p>
							</div>

							<div>
								<h4 className="text-lg font-semibold">
									Ghost (Coming Soon)
								</h4>
								<p className="text-gray-800">
									A word game where players take turns adding
									letters, avoiding completing a valid word.
								</p>
							</div>

							<div>
								<h4 className="text-lg font-semibold">
									Diplomacy (Coming Soon)
								</h4>
								<p className="text-gray-800">
									A game of alliance building and strategic
									elimination featuring LLM players with
									simple identifiers.
								</p>
							</div>

							<div>
								<h4 className="text-lg font-semibold">
									Ultimatum Game (Coming Soon)
								</h4>
								<p className="text-gray-800">
									One player proposes how to split a sum, the
									other accepts or rejects the proposal.
								</p>
							</div>

							<div>
								<h4 className="text-lg font-semibold">
									Rock Paper Scissors (Coming Soon)
								</h4>
								<p className="text-gray-800">
									A multi-round tournament with discussion
									phases before each round.
								</p>
							</div>
						</div>

						<h3 className="text-xl font-semibold mt-6 mb-3">
							Get Involved
						</h3>
						<p className="text-gray-800">
							ParlourBench is an open-source project and welcomes
							contributions. Visit our{" "}
							<a
								href="https://github.com/jmogielnicki/parlourbench/"
								className="text-blue-600 hover:underline"
							>
								GitHub repository
							</a>{" "}
							to learn more about how you can contribute or use
							the benchmark for your own research.
						</p>
					</div>
				</div>
			</div>
		</div>
	);
};

export default AboutParlourBench;