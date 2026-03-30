import { useNavigate } from "react-router-dom";
import DelegationManager from "../components/governance/DelegationManager";
import GovernanceAnalytics from "../components/governance/GovernanceAnalytics";
import GovernanceStats from "../components/governance/GovernanceStats";
import ProposalList from "../components/governance/ProposalList";
import VotingPower from "../components/governance/VotingPower";
import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";

const Analytics = () => {
  const navigate = useNavigate();

  // Sample data - in production this would come from API/contracts
  const governanceData = {
    tokenSymbol: "CFG",
    tokenName: "ChainFinity Governance",
    totalSupply: "100000000",
    quorum: "4",
    votingDelay: "1 day",
    votingPeriod: "7 days",
    proposalThreshold: "0",
    userVotingPower: "1500000",
    userTokenBalance: "1000000",
    delegatedTo: null,
    delegatedFrom: [{ address: "0x1234...5678", amount: "500000" }],
    activeProposals: [
      {
        id: "1",
        title: "Update fee structure for AssetVault",
        description:
          "Proposal to update the fee structure for deposits and withdrawals in the AssetVault contract.",
        proposer: "0xabcd...1234",
        status: "active",
        forVotes: "2500000",
        againstVotes: "1500000",
        abstainVotes: "500000",
        startBlock: "12345678",
        endBlock: "12346678",
        eta: Date.now() + 7 * 24 * 60 * 60 * 1000, // 7 days from now
        executed: false,
      },
      {
        id: "2",
        title: "Add support for Optimism chain",
        description:
          "Proposal to add support for Optimism chain in the CrossChainManager contract.",
        proposer: "0xefgh...5678",
        status: "pending",
        forVotes: "0",
        againstVotes: "0",
        abstainVotes: "0",
        startBlock: "12346700",
        endBlock: "12347700",
        eta: Date.now() + 9 * 24 * 60 * 60 * 1000, // 9 days from now
        executed: false,
      },
    ],
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Governance Analytics</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Comprehensive analytics for ChainFinity governance
          </p>
        </div>
        <div className="mt-4 md:mt-0">
          <Button onClick={() => navigate("/governance")}>
            Back to Governance
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-2">
          <GovernanceAnalytics governanceData={governanceData} />
        </div>
        <div>
          <GovernanceStats
            totalSupply={governanceData.totalSupply}
            votingDelay={governanceData.votingDelay}
            votingPeriod={governanceData.votingPeriod}
            proposalThreshold={governanceData.proposalThreshold}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Recent Proposals</CardTitle>
            </CardHeader>
            <CardContent>
              <ProposalList
                proposals={governanceData.activeProposals}
                onVote={() => {}}
              />
            </CardContent>
          </Card>
        </div>
        <div>
          <Tabs defaultValue="voting" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="voting">Voting Power</TabsTrigger>
              <TabsTrigger value="delegation">Delegation</TabsTrigger>
            </TabsList>

            <TabsContent value="voting" className="mt-4">
              <VotingPower
                userVotingPower={governanceData.userVotingPower}
                userTokenBalance={governanceData.userTokenBalance}
                totalSupply={governanceData.totalSupply}
              />
            </TabsContent>

            <TabsContent value="delegation" className="mt-4">
              <DelegationManager
                delegatedTo={governanceData.delegatedTo}
                delegatedFrom={governanceData.delegatedFrom}
                onDelegate={() => {}}
              />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
