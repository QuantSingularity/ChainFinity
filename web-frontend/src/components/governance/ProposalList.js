import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../../components/ui/card";
import { Progress } from "../../components/ui/progress";
import {
  formatAddress,
  formatDate,
  formatNumber,
} from "../../utils/formatters";

const ProposalList = ({ proposals, onVote }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case "active":
        return "bg-green-500";
      case "pending":
        return "bg-yellow-500";
      case "executed":
        return "bg-blue-500";
      case "defeated":
        return "bg-red-500";
      case "expired":
        return "bg-gray-500";
      default:
        return "bg-gray-300";
    }
  };

  const calculateProgress = (forVotes, againstVotes, abstainVotes) => {
    const total =
      parseFloat(forVotes) +
      parseFloat(againstVotes) +
      parseFloat(abstainVotes);
    if (total === 0)
      return { forPercentage: 0, againstPercentage: 0, abstainPercentage: 0 };

    return {
      forPercentage: (parseFloat(forVotes) / total) * 100,
      againstPercentage: (parseFloat(againstVotes) / total) * 100,
      abstainPercentage: (parseFloat(abstainVotes) / total) * 100,
    };
  };

  const handleVote = async (proposalId, support) => {
    try {
      await onVote(proposalId, support);
    } catch (error) {
      console.error("Error voting:", error);
    }
  };

  if (!proposals || proposals.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <p className="text-gray-500">No proposals found</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {proposals.map((proposal) => {
        const { forPercentage, againstPercentage, abstainPercentage } =
          calculateProgress(
            proposal.forVotes,
            proposal.againstVotes,
            proposal.abstainVotes,
          );

        return (
          <Card key={proposal.id} className="overflow-hidden">
            <div className="flex items-center p-1">
              <div
                className={`w-2 h-full ${getStatusColor(proposal.status)}`}
              ></div>
              <CardHeader className="py-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-xl">{proposal.title}</CardTitle>
                  <Badge
                    variant={
                      proposal.status === "active" ? "default" : "outline"
                    }
                  >
                    {proposal.status.charAt(0).toUpperCase() +
                      proposal.status.slice(1)}
                  </Badge>
                </div>
              </CardHeader>
            </div>

            <CardContent className="pb-6">
              <div className="mb-4">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  {proposal.description.length > 200
                    ? `${proposal.description.substring(0, 200)}...`
                    : proposal.description}
                </p>
                <div className="flex items-center text-xs text-gray-500">
                  <span>Proposed by {formatAddress(proposal.proposer)}</span>
                  <span className="mx-2">•</span>
                  <span>Ends {formatDate(proposal.eta)}</span>
                </div>
              </div>

              <div className="space-y-3 mb-6">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-xs">For</span>
                    <span className="text-xs">
                      {formatNumber(proposal.forVotes)}
                    </span>
                  </div>
                  <Progress
                    value={forPercentage}
                    className="h-1 bg-gray-200"
                    indicatorColor="bg-green-500"
                  />
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-xs">Against</span>
                    <span className="text-xs">
                      {formatNumber(proposal.againstVotes)}
                    </span>
                  </div>
                  <Progress
                    value={againstPercentage}
                    className="h-1 bg-gray-200"
                    indicatorColor="bg-red-500"
                  />
                </div>

                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-xs">Abstain</span>
                    <span className="text-xs">
                      {formatNumber(proposal.abstainVotes)}
                    </span>
                  </div>
                  <Progress
                    value={abstainPercentage}
                    className="h-1 bg-gray-200"
                    indicatorColor="bg-gray-500"
                  />
                </div>
              </div>

              {proposal.status === "active" && (
                <div className="flex space-x-2">
                  <Button
                    variant="default"
                    className="flex-1"
                    onClick={() => handleVote(proposal.id, 1)}
                  >
                    Vote For
                  </Button>
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => handleVote(proposal.id, 0)}
                  >
                    Vote Against
                  </Button>
                  <Button
                    variant="ghost"
                    className="flex-1"
                    onClick={() => handleVote(proposal.id, 2)}
                  >
                    Abstain
                  </Button>
                </div>
              )}

              {proposal.status === "succeeded" && !proposal.executed && (
                <Button className="w-full">Execute Proposal</Button>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

export default ProposalList;
