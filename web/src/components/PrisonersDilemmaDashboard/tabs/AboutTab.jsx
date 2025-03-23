import React from "react";

/**
 * About Tab content with information about the Prisoner's Dilemma game
 */
const AboutTab = () => {
	return (
		<div className="space-y-6">
			<div className="bg-white rounded-lg shadow-md overflow-hidden">
				<div className="px-6 py-4 border-b border-gray-200">
					<h2 className="text-xl font-semibold">
						About Prisoner's Dilemma
					</h2>
				</div>
				<div className="p-6">
					<div className="prose prose-lg max-w-none text-left">
						<p className="text-gray-800">
							The Prisoner's Dilemma is a classic game theory
							scenario that demonstrates why two completely
							rational individuals might not cooperate, even if it
							appears that it's in their best interests to do so.
							In this case, two AI models played 5 rounds of
							Prisoner's Dilemma and were told to try to maximize
							their score.
						</p>
						<h3 className="text-xl font-semibold mt-6 mb-3">
							Game Structure
						</h3>
						<ul className="list-disc pl-6 space-y-2">
							<li className="text-gray-800">
								<span className="font-semibold">Players:</span>{" "}
								2 LLMs compete against each other
							</li>
							<li className="text-gray-800">
								<span className="font-semibold">Rounds:</span> 5
								rounds per game
							</li>
							<li className="text-gray-800">
								<span className="font-semibold">Choices:</span>{" "}
								Cooperate or Defect (made simultaneously)
							</li>
							<li className="text-gray-800">
								<span className="font-semibold">Scoring:</span>
								<ul className="list-disc pl-6 mt-2 space-y-1">
									<li>Both cooperate: 3 points each</li>
									<li>Both defect: 1 point each</li>
									<li>
										One defects, one cooperates: Defector
										gets 5 points, cooperator gets 0
									</li>
								</ul>
							</li>
							<li className="text-gray-800">
								<span className="font-semibold">Winning:</span>{" "}
								The model with the higher score at the end of
								the game wins
							</li>
						</ul>

						<h3 className="text-xl font-semibold mt-6 mb-3">
							Why This Game Matters
						</h3>
						<p className="text-gray-800">
							The Prisoner's Dilemma tests AI models' strategic
							decision-making by challenging them to identify
							optimal defection timing for maximizing their score. Models
							may win individual games yet lose tournaments by
							defecting too early, triggering tit-for-tat cycles
							that reduce both players' scores. Analyzing their
							reasoning provides insights into each model's
							trust/paranoia levels and cooperation/opposition
							tendencies.
						</p>
					</div>
				</div>
			</div>
		</div>
	);
};

export default AboutTab;
