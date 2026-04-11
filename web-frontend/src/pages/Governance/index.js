import {
  AccountBalanceWallet as WalletIcon,
  HowToVote as VoteIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
} from "@mui/icons-material";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  Grid,
  LinearProgress,
  Paper,
  Tab,
  Tabs,
  Typography,
  useTheme,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { motion } from "framer-motion";
import { useState } from "react";
import { useApp } from "../../context/AppContext";
import GovernanceStats from "../../components/governance/GovernanceStats";
import VotingPower from "../../components/governance/VotingPower";
import DelegationManager from "../../components/governance/DelegationManager";
import ProposalList from "../../components/governance/ProposalList";
import CreateProposal from "../../components/governance/CreateProposal";

const TabPanel = ({ children, value, index, ...other }) => (
  <div
    role="tabpanel"
    hidden={value !== index}
    id={`governance-tabpanel-${index}`}
    aria-labelledby={`governance-tab-${index}`}
    {...other}
  >
    {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
  </div>
);

const MOCK_PROPOSALS = [
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
    eta: Date.now() + 7 * 24 * 60 * 60 * 1000,
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
    eta: Date.now() + 9 * 24 * 60 * 60 * 1000,
    executed: false,
  },
];

const MOCK_GOVERNANCE_DATA = {
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
  activeProposals: MOCK_PROPOSALS,
};

const Governance = () => {
  const theme = useTheme();
  const { isAuthenticated, user } = useApp();
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [actionFeedback, setActionFeedback] = useState(null);
  const [governanceData] = useState(MOCK_GOVERNANCE_DATA);

  const showFeedback = (message, severity = "success") => {
    setActionFeedback({ message, severity });
    setTimeout(() => setActionFeedback(null), 4000);
  };

  const handleCreateProposal = async (proposalData) => {
    setLoading(true);
    try {
      await new Promise((res) => setTimeout(res, 800));
      showFeedback(`Proposal "${proposalData.title}" submitted successfully!`);
      setTabValue(0);
    } catch {
      showFeedback("Failed to submit proposal. Please try again.", "error");
    } finally {
      setLoading(false);
    }
    return true;
  };

  const handleVote = async (proposalId, support) => {
    setLoading(true);
    try {
      await new Promise((res) => setTimeout(res, 800));
      const voteLabel =
        support === 1 ? "For" : support === 0 ? "Against" : "Abstain";
      showFeedback(`Vote "${voteLabel}" cast on proposal #${proposalId}!`);
    } catch {
      showFeedback("Failed to cast vote. Please try again.", "error");
    } finally {
      setLoading(false);
    }
    return true;
  };

  const handleDelegate = async (delegatee) => {
    setLoading(true);
    try {
      await new Promise((res) => setTimeout(res, 800));
      showFeedback(`Voting power delegated to ${delegatee}!`);
    } catch {
      showFeedback("Failed to delegate. Please try again.", "error");
    } finally {
      setLoading(false);
    }
    return true;
  };

  if (!isAuthenticated) {
    return (
      <Container maxWidth="md" sx={{ py: 8 }}>
        <Card sx={{ textAlign: "center", p: 6 }}>
          <CardContent>
            <WalletIcon sx={{ fontSize: 64, color: "primary.main", mb: 2 }} />
            <Typography variant="h5" fontWeight={700} gutterBottom>
              Governance Dashboard
            </Typography>
            <Typography color="text.secondary" sx={{ mb: 4 }}>
              Sign in to view and participate in ChainFinity governance
            </Typography>
            <Button
              variant="contained"
              size="large"
              href="/login"
              startIcon={<WalletIcon />}
            >
              Sign In to Participate
            </Button>
          </CardContent>
        </Card>
      </Container>
    );
  }

  return (
    <Box sx={{ py: 4 }}>
      <Container maxWidth="lg">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          {/* Header */}
          <Box
            sx={{
              mb: 4,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              flexWrap: "wrap",
              gap: 2,
            }}
          >
            <Box>
              <Typography variant="h4" fontWeight={700} gutterBottom>
                Governance Dashboard
              </Typography>
              <Typography color="text.secondary">
                Participate in the decentralized governance of ChainFinity
              </Typography>
            </Box>
            <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
              <Chip
                label={`${governanceData.tokenName} (${governanceData.tokenSymbol})`}
                variant="outlined"
                color="primary"
              />
              <Chip
                label={`Quorum: ${governanceData.quorum}%`}
                color="secondary"
              />
            </Box>
          </Box>

          {/* Feedback alert */}
          {actionFeedback && (
            <Alert
              severity={actionFeedback.severity}
              sx={{ mb: 3 }}
              onClose={() => setActionFeedback(null)}
            >
              {actionFeedback.message}
            </Alert>
          )}

          {loading && <LinearProgress sx={{ mb: 2, borderRadius: 1 }} />}

          {/* Stats Row */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={4}>
              <GovernanceStats
                totalSupply={governanceData.totalSupply}
                votingDelay={governanceData.votingDelay}
                votingPeriod={governanceData.votingPeriod}
                proposalThreshold={governanceData.proposalThreshold}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <VotingPower
                userVotingPower={governanceData.userVotingPower}
                userTokenBalance={governanceData.userTokenBalance}
                totalSupply={governanceData.totalSupply}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <DelegationManager
                delegatedTo={governanceData.delegatedTo}
                delegatedFrom={governanceData.delegatedFrom}
                onDelegate={handleDelegate}
              />
            </Grid>
          </Grid>

          {/* Tabs */}
          <Paper
            sx={{
              borderRadius: 3,
              border: `1px solid ${theme.palette.divider}`,
              overflow: "hidden",
            }}
          >
            <Box sx={{ borderBottom: 1, borderColor: "divider", px: 3, pt: 1 }}>
              <Tabs
                value={tabValue}
                onChange={(_, v) => setTabValue(v)}
                aria-label="governance tabs"
              >
                <Tab
                  label="Proposals"
                  icon={<VoteIcon />}
                  iconPosition="start"
                  id="governance-tab-0"
                  aria-controls="governance-tabpanel-0"
                />
                <Tab
                  label="Create Proposal"
                  icon={<AddIcon />}
                  iconPosition="start"
                  id="governance-tab-1"
                  aria-controls="governance-tabpanel-1"
                />
              </Tabs>
            </Box>

            <Box sx={{ p: 3 }}>
              <TabPanel value={tabValue} index={0}>
                <ProposalList
                  proposals={governanceData.activeProposals}
                  onVote={handleVote}
                />
              </TabPanel>
              <TabPanel value={tabValue} index={1}>
                <CreateProposal onSubmit={handleCreateProposal} />
              </TabPanel>
            </Box>
          </Paper>
        </motion.div>
      </Container>
    </Box>
  );
};

export default Governance;
