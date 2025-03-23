import React from "react";
import { Scale, MessageCircle, Vote, RefreshCw } from "lucide-react";

/**
 * About Tab content with information about the Debate Slam game
 */
const AboutTab = () => {
	return (
		<div className="space-y-6">
			<div className="bg-white rounded-lg shadow-md overflow-hidden">
				<div className="px-6 py-4 border-b border-gray-200">
					<h2 className="text-xl font-semibold">About Debate Slam</h2>
				</div>
				<div className="p-6">
					<div className="prose prose-lg max-w-none text-left">
						<p className="text-gray-800">
							Debate Slam is a competitive discourse benchmark
							that evaluates language models' ability to construct
							persuasive arguments, respond to counterpoints, and
							articulate complex positions. This game tests
							models' persuasiveness, logical reasoning, and
							adaptability across different positions, all judged
							by peer models.
						</p>

						<h3 className="text-xl font-semibold mt-6 mb-3">
							Game Description
						</h3>
						<p className="text-gray-800">
							Played with 7 participants: 2 models assigned as
							debaters and 5 models assigned as judges. Debaters
							are assigned opposite sides of a pre-established
							debate topic. After arguing over 3 rounds, the
							entire debate is repeated with debaters switching
							sides to ensure fairness. Scoring is based on judge
							votes from both runs, testing models' persuasive
							capabilities regardless of position.
						</p>

						<h3 className="text-xl font-semibold mt-6 mb-3">
							Game Structure
						</h3>
						<div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
							<div className="border rounded-lg p-4 bg-gray-50">
								<div className="flex items-center mb-2">
									<Scale className="w-5 h-5 mr-2 text-blue-600" />
									<h4 className="font-medium text-lg">
										Setup Phase
									</h4>
								</div>
								<p className="text-gray-700">
									A debate topic is established and models are
									assigned roles. Two models become debaters,
									each assigned to opposing sides of the
									topic, while the remaining five models serve
									as judges.
								</p>
							</div>

							<div className="border rounded-lg p-4 bg-gray-50">
								<div className="flex items-center mb-2">
									<MessageCircle className="w-5 h-5 mr-2 text-green-600" />
									<h4 className="font-medium text-lg">
										Debate Phase
									</h4>
								</div>
								<p className="text-gray-700">
									Debaters engage in a structured argument
									over three rounds, presenting their
									positions, addressing counterarguments, and
									delivering concluding statements.
								</p>
							</div>

							<div className="border rounded-lg p-4 bg-gray-50">
								<div className="flex items-center mb-2">
									<Vote className="w-5 h-5 mr-2 text-purple-600" />
									<h4 className="font-medium text-lg">
										Judging Phase
									</h4>
								</div>
								<p className="text-gray-700">
									After each round, judges independently
									decide which side made the more persuasive
									argument. After the final round, judges make
									their final decisions, determining which
									debater was most persuasive.
								</p>
							</div>

							<div className="border rounded-lg p-4 bg-gray-50">
								<div className="flex items-center mb-2">
									<RefreshCw className="w-5 h-5 mr-2 text-amber-600" />
									<h4 className="font-medium text-lg">
										Side-Switching Phase
									</h4>
								</div>
								<p className="text-gray-700">
									To ensure fairness, the entire debate is run
									again with debaters switching sides. This
									tests each model's ability to argue
									persuasively regardless of position. Final
									scores combine judge votes from both debate
									sessions.
								</p>
							</div>
						</div>

						<p className="text-gray-800 mt-4">
							Debate Slam measures a model's persuasiveness and
							adaptability. If a model can convince judges of both
							sides of an argument, it demonstrates intellectual
							flexibility, nuanced understanding of complex
							issues, and an ability to communicate and convince.
							As these models become increasingly integrated into
							information ecosystems, it is important to measure their persuasive
							power.  The tools we create can also shape us.
						</p>
					</div>
				</div>
			</div>
		</div>
	);
};

export default AboutTab;
