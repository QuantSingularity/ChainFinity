import { ArrowBack as BackIcon, Analytics as AnalyticsIcon } from "@mui/icons-material";
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Grid,
  Tab,
  Tabs,
  Typography,
  useTheme,
} from "@mui/material";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import DelegationManager from "../../components/governance/DelegationManager";
import GovernanceAnalytics from "../../components/governance/GovernanceAnalytics";
import GovernanceStats from "../../components/governance/GovernanceStats";
import ProposalList from "../../components/governance/ProposalList";
import VotingPower from "../../components/governance/VotingPower";

const GOVERNANCE_DATA = {
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
      description: "Proposal to update the fee structure for deposits and withdrawals.",
      proposer: "0xabcd...1234",
      status: "active",
      forVotes: "2500000",
      againstVotes: "1500000",
      abstainVotes: "500000",
      startBlock: "12345678",
      endBlock: "12346678",
      eta: Date.now() + 7 * 24 * 60 * 60 * 1000,
      executed: false,
    },
    {
      id: "2",
      title: "Add support for Optimism chain",
      description: "Proposal to add Optimism support in CrossChainManager.",
      proposer: "0xefgh...5678",
      status: "pending",
      forVotes: "0",
      againstVotes: "0",
      abstainVotes: "0",
      startBlock: "12346700",
      endBlock: "12347700",
      eta: Date.now() + 9 * 24 * 60 * 60 * 1000,
      executed: false,
    },
  ],
};

const Analytics = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const [sideTab, setSideTab] = useState(0);
  const governanceData = GOVERNANCE_DATA;

  return (
    <Box sx={{ py: 4 }}>
      <Container maxWidth="lg">
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            mb: 4,
            flexWrap: "wrap",
            gap: 2,
          }}
        >
          <Box>
            <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
              <AnalyticsIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h4" fontWeight={700}>
                Governance Analytics
              </Typography>
            </Box>
            <Typography color="text.secondary">
              Comprehensive analytics for ChainFinity governance
            </Typography>
          </Box>
          <Button
            variant="outlined"
            startIcon={<BackIcon />}
            onClick={() => navigate("/governance")}
          >
            Back to Governance
          </Button>
        </Box>

        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} lg={8}>
            <GovernanceAnalytics governanceData={governanceData} />
          </Grid>
          <Grid item xs={12} lg={4}>
            <GovernanceStats
              totalSupply={governanceData.totalSupply}
              votingDelay={governanceData.votingDelay}
              votingPeriod={governanceData.votingPeriod}
              proposalThreshold={governanceData.proposalThreshold}
            />
          </Grid>
        </Grid>

        <Grid container spacing={3}>
          <Grid item xs={12} lg={8}>
            <Card sx={{ border: `1px solid ${theme.palette.divider}`, boxShadow: "none" }}>
              <CardContent>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  Recent Proposals
                </Typography>
                <ProposalList
                  proposals={governanceData.activeProposals}
                  onVote={() => {}}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} lg={4}>
            <Card sx={{ border: `1px solid ${theme.palette.divider}`, boxShadow: "none" }}>
              <CardContent>
                <Tabs
                  value={sideTab}
                  onChange={(_, v) => setSideTab(v)}
                  sx={{ mb: 2 }}
                >
                  <Tab label="Voting Power" />
                  <Tab label="Delegation" />
                </Tabs>
                {sideTab === 0 && (
                  <VotingPower
                    userVotingPower={governanceData.userVotingPower}
                    userTokenBalance={governanceData.userTokenBalance}
                    totalSupply={governanceData.totalSupply}
                  />
                )}
                {sideTab === 1 && (
                  <DelegationManager
                    delegatedTo={governanceData.delegatedTo}
                    delegatedFrom={governanceData.delegatedFrom}
                    onDelegate={() => {}}
                  />
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default Analytics;
