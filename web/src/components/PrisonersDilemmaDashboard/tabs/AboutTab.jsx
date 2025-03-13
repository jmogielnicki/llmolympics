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
						</p>

						<h3 className="text-xl font-semibold mt-6 mb-3">
							Game Description
						</h3>
						<p className="text-gray-800">
							Players participate in multiple rounds of the
							classic dilemma against different opponents. Each
							round, players simultaneously choose to cooperate or
							defect. Mutual cooperation yields moderate rewards
							for both (3,3), mutual defection yields low rewards
							(1,1), while unilateral defection yields high reward
							for the defector (5,0). Different strategies emerge
							across repeated interactions.
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
						</ul>

						<h3 className="text-xl font-semibold mt-6 mb-3">
							Why This Game Matters
						</h3>
						<p className="text-gray-800">
							The Prisoner's Dilemma tests an AI model's ability
							to make strategic decisions when there are
							trade-offs between short-term gain and long-term
							cooperation. It can reveal whether models are
							capable of developing trust, recognizing patterns in
							opponent behavior, and adapting strategies
							accordingly.
						</p>
					</div>
				</div>
			</div>
		</div>
	);
};

export default AboutTab;
