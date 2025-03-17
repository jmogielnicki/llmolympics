import React from "react";
import { Award, ThumbsUp } from "lucide-react";
import { shortenModelName } from "../../../utils/commonUtils";
import ReactMarkdown from "react-markdown";

/**
 * Component to display a poem with voting information
 *
 * @param {Object} props
 * @param {Object} props.poem - The poem data
 * @param {string} props.poem.text - The poem text
 * @param {string} props.poem.author - The model name that authored the poem
 * @param {number} props.poem.votes - Number of votes received
 * @param {boolean} props.poem.isWinner - Whether this poem was the winner
 * @param {Array} props.poem.votedBy - Array of model names that voted for this poem
 */
const PoemDisplay = ({ poem, showBorder = true }) => {
	if (!poem) return null;

	return (
		<div
			className={`${
				showBorder ? "border border-gray-200" : ""
			} rounded-md overflow-hidden h-full`}
		>
			<div className="flex items-center justify-between p-3 border-b border-gray-200 bg-gray-50">
				<div className="flex items-center gap-2">
					<span className="font-medium">
						{shortenModelName(poem.author)}
					</span>
					{poem.isWinner && (
						<span
							className="flex items-center text-amber-600"
							title="Winner"
						>
							<Award size={16} className="mr-1" />
							<span className="text-xs font-medium">Winner</span>
						</span>
					)}
				</div>
				{poem.votes > 0 && (
					<span className="flex items-center text-blue-600 bg-blue-50 px-2 py-1 rounded text-xs">
						<ThumbsUp size={14} className="mr-1" />
						{poem.votes} vote{poem.votes !== 1 ? "s" : ""}
					</span>
				)}
			</div>

			<div className="p-4 prose prose-sm max-w-none bg-white">
				<div className="whitespace-pre-line">
					<ReactMarkdown>
						{poem.text.replace(/  \n/g, "\n")}
					</ReactMarkdown>
				</div>
			</div>

			{poem.votedBy && poem.votedBy.length > 0 && (
				<div className="px-3 py-2 border-t border-gray-200 bg-gray-50 text-xs text-gray-500">
					<p className="mb-1">Voted for by:</p>
					<div className="flex flex-wrap gap-1">
						{poem.votedBy.map((voter, index) => (
							<span
								key={index}
								className="inline-flex items-center px-2 py-1 rounded bg-blue-100 text-blue-800"
							>
								{shortenModelName(voter)}
							</span>
						))}
					</div>
				</div>
			)}
		</div>
	);
};

export default PoemDisplay;
