import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import CreateProposal from "../components/governance/CreateProposal";
import DelegationManager from "../components/governance/DelegationManager";
import GovernanceStats from "../components/governance/GovernanceStats";
import ProposalList from "../components/governance/ProposalList";
import VotingPower from "../components/governance/VotingPower";
import { Badge } from "../components/ui/badge";
import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Loader } from "../components/ui/loader";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import { useWeb3Context } from "../context/Web3Context";

const Governance = () => {
  const _navigate = useNavigate();
  const { account, provider, chainId, connectWallet } = useWeb3Context();
  const [activeTab, setActiveTab] = useState("proposals");
  const [loading, setLoading] = useState(true);
  const [governanceData, setGovernanceData] = useState({
    tokenSymbol: "CFG",
    tokenName: "ChainFinity Governance",
    totalSupply: "100000000",
    quorum: "4",
    votingDelay: "1 day",
    votingPeriod: "7 days",
    proposalThreshold: "0",
    activeProposals: [],
    userVotingPower: "0",
    userTokenBalance: "0",
    delegatedTo: null,
    delegatedFrom: [],
  });

  useEffect(() => {
    const fetchGovernanceData = async () => {
      if (!account || !provider) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        // This would be replaced with actual contract calls in production
        // Simulating data fetch for now
        setTimeout(() => {
          setGovernanceData({
            ...governanceData,
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
          });
          setLoading(false);
        }, 1000);
      } catch (error) {
        console.error("Error fetching governance data:", error);
        setLoading(false);
      }
    };

    fetchGovernanceData();
  }, [account, provider, governanceData]);

  const handleCreateProposal = async (proposalData) => {
    // This would be replaced with actual contract calls in production
    console.log("Creating proposal:", proposalData);
    // Simulate success
    return true;
  };

  const handleVote = async (proposalId, support) => {
    // This would be replaced with actual contract calls in production
    console.log(`Voting on proposal ${proposalId} with support ${support}`);
    // Simulate success
    return true;
  };

  const handleDelegate = async (delegatee) => {
    // This would be replaced with actual contract calls in production
    console.log(`Delegating to ${delegatee}`);
    // Simulate success
    return true;
  };

  if (!account) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card className="w-full max-w-4xl mx-auto">
          <CardHeader>
            <CardTitle className="text-2xl">Governance Dashboard</CardTitle>
            <CardDescription>
              Connect your wallet to access the ChainFinity governance platform
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <p className="mb-6 text-center text-gray-600 dark:text-gray-400">
              You need to connect your wallet to view and participate in
              governance
            </p>
            <Button onClick={connectWallet} size="lg">
              Connect Wallet
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Governance Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Participate in the decentralized governance of ChainFinity
          </p>
        </div>
        <div className="mt-4 md:mt-0">
          <Badge variant="outline" className="mr-2">
            {governanceData.tokenName} ({governanceData.tokenSymbol})
          </Badge>
          <Badge variant="secondary">Quorum: {governanceData.quorum}%</Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <GovernanceStats
          totalSupply={governanceData.totalSupply}
          votingDelay={governanceData.votingDelay}
          votingPeriod={governanceData.votingPeriod}
          proposalThreshold={governanceData.proposalThreshold}
        />

        <VotingPower
          userVotingPower={governanceData.userVotingPower}
          userTokenBalance={governanceData.userTokenBalance}
          totalSupply={governanceData.totalSupply}
        />

        <DelegationManager
          delegatedTo={governanceData.delegatedTo}
          delegatedFrom={governanceData.delegatedFrom}
          onDelegate={handleDelegate}
        />
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="proposals">Proposals</TabsTrigger>
          <TabsTrigger value="create">Create Proposal</TabsTrigger>
        </TabsList>

        <TabsContent value="proposals" className="mt-6">
          {loading ? (
            <div className="flex justify-center py-12">
              <Loader size="lg" />
            </div>
          ) : (
            <ProposalList
              proposals={governanceData.activeProposals}
              onVote={handleVote}
            />
          )}
        </TabsContent>

        <TabsContent value="create" className="mt-6">
          <CreateProposal onSubmit={handleCreateProposal} />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Governance;
