import {
  ArrowDownward,
  ArrowUpward,
  FilterList,
  GetApp,
  MoreVert,
  Refresh,
  Search,
  SwapHoriz,
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
  Divider,
  FormControl,
  Grid,
  IconButton,
  InputAdornment,
  InputLabel,
  MenuItem,
  Pagination,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { AdapterDateFns } from "@mui/x-date-pickers/AdapterDateFns";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { motion } from "framer-motion";
import { useState } from "react";
import { useApp } from "../context/AppContext";
import { useTransactionHistory } from "../hooks/useProtocolData";

const StyledTableCell = styled(TableCell)(({ theme }) => ({
  borderBottom: `1px solid ${theme.palette.divider}`,
  padding: theme.spacing(2),
}));

const StyledTableRow = styled(TableRow)(({ theme }) => ({
  "&:hover": {
    backgroundColor:
      theme.palette.mode === "light"
        ? "rgba(0, 0, 0, 0.04)"
        : "rgba(255, 255, 255, 0.04)",
  },
}));

const FilterCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(3),
  borderRadius: theme.shape.borderRadius,
  boxShadow: "none",
  border: `1px solid ${theme.palette.divider}`,
}));

const Transactions = () => {
  const theme = useTheme();
  const { user } = useApp();
  const [page, setPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(5);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [networkFilter, setNetworkFilter] = useState("all");
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [showFilters, setShowFilters] = useState(false);

  // Get wallet address from user context
  const walletAddress = user?.wallet_address;

  // Fetch transaction history
  const { transactions, loading, error, refreshTransactions } =
    useTransactionHistory(walletAddress);

  // Redirect to login if not authenticated
  const handleChangePage = (_event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(1);
  };

  const handleSearchChange = (event) => {
    setSearchQuery(event.target.value);
    setPage(1);
  };

  const handleTypeFilterChange = (event) => {
    setTypeFilter(event.target.value);
    setPage(1);
  };

  const handleNetworkFilterChange = (event) => {
    setNetworkFilter(event.target.value);
    setPage(1);
  };

  const handleStartDateChange = (date) => {
    setStartDate(date);
    setPage(1);
  };

  const handleEndDateChange = (date) => {
    setEndDate(date);
    setPage(1);
  };

  const toggleFilters = () => {
    setShowFilters(!showFilters);
  };

  const resetFilters = () => {
    setSearchQuery("");
    setTypeFilter("all");
    setNetworkFilter("all");
    setStartDate(null);
    setEndDate(null);
    setPage(1);
  };

  // Filter transactions based on search query and filters
  const filteredTransactions = transactions
    ? transactions.filter((transaction) => {
        // Search query filter
        if (
          searchQuery &&
          !Object.values(transaction).some((value) =>
            String(value).toLowerCase().includes(searchQuery.toLowerCase()),
          )
        ) {
          return false;
        }

        // Type filter
        if (typeFilter !== "all" && transaction.type !== typeFilter) {
          return false;
        }

        // Network filter
        if (networkFilter !== "all" && transaction.network !== networkFilter) {
          return false;
        }

        // Date range filter
        if (startDate && new Date(transaction.date) < startDate) {
          return false;
        }

        if (endDate && new Date(transaction.date) > endDate) {
          return false;
        }

        return true;
      })
    : [];

  // Pagination
  const paginatedTransactions = filteredTransactions.slice(
    (page - 1) * rowsPerPage,
    (page - 1) * rowsPerPage + rowsPerPage,
  );

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.5,
      },
    },
  };

  if (loading) {
    return (
      <Box sx={{ width: "100%", mt: 4 }}>
        <Container maxWidth="lg">
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              flexDirection: "column",
              py: 8,
            }}
          >
            <CircularProgress size={60} />
            <Typography variant="h6" sx={{ mt: 2 }}>
              Loading transactions...
            </Typography>
          </Box>
        </Container>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ width: "100%", mt: 4 }}>
        <Container maxWidth="lg">
          <Alert severity="error" sx={{ mb: 2 }}>
            {error.message ||
              "An error occurred while loading your transactions."}
          </Alert>
          <Button
            variant="contained"
            onClick={refreshTransactions}
            startIcon={<Refresh />}
          >
            Try Again
          </Button>
        </Container>
      </Box>
    );
  }

  return (
    <Box sx={{ py: 4 }}>
      <Container maxWidth="lg">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Header */}
          <motion.div variants={itemVariants}>
            <Box
              sx={{
                mb: 4,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <Box>
                <Typography variant="h4" component="h1" fontWeight={700}>
                  Transactions
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  View and manage your transaction history
                </Typography>
              </Box>
              <Button
                variant="contained"
                startIcon={<GetApp />}
                sx={{
                  borderRadius: "12px",
                  boxShadow: "none",
                }}
              >
                Export CSV
              </Button>
            </Box>
          </motion.div>

          {/* Search and Filters */}
          <motion.div variants={itemVariants}>
            <Box sx={{ mb: 3 }}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    placeholder="Search transactions..."
                    value={searchQuery}
                    onChange={handleSearchChange}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Search color="action" />
                        </InputAdornment>
                      ),
                    }}
                  />
                </Grid>
                <Grid
                  item
                  xs={12}
                  md={6}
                  sx={{
                    display: "flex",
                    justifyContent: { xs: "flex-start", md: "flex-end" },
                  }}
                >
                  <Button
                    variant="outlined"
                    startIcon={<FilterList />}
                    onClick={toggleFilters}
                    sx={{ mr: 2 }}
                  >
                    Filters
                  </Button>
                  <FormControl sx={{ minWidth: 120 }}>
                    <InputLabel id="rows-per-page-label">Show</InputLabel>
                    <Select
                      labelId="rows-per-page-label"
                      value={rowsPerPage}
                      label="Show"
                      onChange={handleChangeRowsPerPage}
                    >
                      <MenuItem value={5}>5</MenuItem>
                      <MenuItem value={10}>10</MenuItem>
                      <MenuItem value={25}>25</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </Box>
          </motion.div>

          {/* Advanced Filters */}
          {showFilters && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
            >
              <FilterCard>
                <CardContent>
                  <Grid container spacing={3}>
                    <Grid item xs={12} sm={6} md={3}>
                      <FormControl fullWidth>
                        <InputLabel id="type-filter-label">Type</InputLabel>
                        <Select
                          labelId="type-filter-label"
                          value={typeFilter}
                          label="Type"
                          onChange={handleTypeFilterChange}
                        >
                          <MenuItem value="all">All Types</MenuItem>
                          <MenuItem value="send">Send</MenuItem>
                          <MenuItem value="receive">Receive</MenuItem>
                          <MenuItem value="swap">Swap</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <FormControl fullWidth>
                        <InputLabel id="network-filter-label">
                          Network
                        </InputLabel>
                        <Select
                          labelId="network-filter-label"
                          value={networkFilter}
                          label="Network"
                          onChange={handleNetworkFilterChange}
                        >
                          <MenuItem value="all">All Networks</MenuItem>
                          <MenuItem value="Ethereum">Ethereum</MenuItem>
                          <MenuItem value="Polygon">Polygon</MenuItem>
                          <MenuItem value="Bitcoin">Bitcoin</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <LocalizationProvider dateAdapter={AdapterDateFns}>
                        <DatePicker
                          label="Start Date"
                          value={startDate}
                          onChange={handleStartDateChange}
                          renderInput={(params) => (
                            <TextField {...params} fullWidth />
                          )}
                        />
                      </LocalizationProvider>
                    </Grid>
                    <Grid item xs={12} sm={6} md={3}>
                      <LocalizationProvider dateAdapter={AdapterDateFns}>
                        <DatePicker
                          label="End Date"
                          value={endDate}
                          onChange={handleEndDateChange}
                          renderInput={(params) => (
                            <TextField {...params} fullWidth />
                          )}
                        />
                      </LocalizationProvider>
                    </Grid>
                  </Grid>
                  <Box
                    sx={{ display: "flex", justifyContent: "flex-end", mt: 2 }}
                  >
                    <Button
                      variant="text"
                      color="inherit"
                      onClick={resetFilters}
                      sx={{ mr: 2 }}
                    >
                      Reset Filters
                    </Button>
                    <Button variant="contained" onClick={toggleFilters}>
                      Apply Filters
                    </Button>
                  </Box>
                </CardContent>
              </FilterCard>
            </motion.div>
          )}

          {/* Transactions Table */}
          <motion.div variants={itemVariants}>
            <Paper
              sx={{
                borderRadius: theme.shape.borderRadius,
                overflow: "hidden",
                mb: 3,
              }}
            >
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <StyledTableCell>Type</StyledTableCell>
                      <StyledTableCell>Asset</StyledTableCell>
                      <StyledTableCell>Amount</StyledTableCell>
                      <StyledTableCell>Value</StyledTableCell>
                      <StyledTableCell>Date & Time</StyledTableCell>
                      <StyledTableCell>Network</StyledTableCell>
                      <StyledTableCell>Status</StyledTableCell>
                      <StyledTableCell align="right">Actions</StyledTableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {paginatedTransactions.length > 0 ? (
                      paginatedTransactions.map((transaction) => (
                        <StyledTableRow key={transaction.id}>
                          <StyledTableCell>
                            <Box
                              sx={{
                                display: "flex",
                                alignItems: "center",
                              }}
                            >
                              {transaction.type === "receive" && (
                                <Chip
                                  icon={<ArrowDownward />}
                                  label="Receive"
                                  color="success"
                                  size="small"
                                  sx={{ minWidth: "90px" }}
                                />
                              )}
                              {transaction.type === "send" && (
                                <Chip
                                  icon={<ArrowUpward />}
                                  label="Send"
                                  color="error"
                                  size="small"
                                  sx={{ minWidth: "90px" }}
                                />
                              )}
                              {transaction.type === "swap" && (
                                <Chip
                                  icon={<SwapHoriz />}
                                  label="Swap"
                                  color="info"
                                  size="small"
                                  sx={{ minWidth: "90px" }}
                                />
                              )}
                            </Box>
                          </StyledTableCell>
                          <StyledTableCell>{transaction.asset}</StyledTableCell>
                          <StyledTableCell>
                            {transaction.amount}
                          </StyledTableCell>
                          <StyledTableCell>{transaction.value}</StyledTableCell>
                          <StyledTableCell>
                            <Box
                              sx={{
                                display: "flex",
                                flexDirection: "column",
                              }}
                            >
                              <Typography variant="body2">
                                {transaction.date}
                              </Typography>
                              <Typography
                                variant="caption"
                                color="text.secondary"
                              >
                                {transaction.time}
                              </Typography>
                            </Box>
                          </StyledTableCell>
                          <StyledTableCell>
                            <Chip
                              label={transaction.network}
                              variant="outlined"
                              size="small"
                            />
                          </StyledTableCell>
                          <StyledTableCell>
                            <Chip
                              label={transaction.status}
                              color="success"
                              size="small"
                              variant="outlined"
                            />
                          </StyledTableCell>
                          <StyledTableCell align="right">
                            <IconButton size="small">
                              <MoreVert fontSize="small" />
                            </IconButton>
                          </StyledTableCell>
                        </StyledTableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={8} align="center" sx={{ py: 3 }}>
                          <Typography variant="body1" color="text.secondary">
                            No transactions found
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>

              {/* Pagination */}
              {filteredTransactions.length > 0 && (
                <Box sx={{ display: "flex", justifyContent: "flex-end", p: 2 }}>
                  <Pagination
                    count={Math.ceil(filteredTransactions.length / rowsPerPage)}
                    page={page}
                    onChange={handleChangePage}
                    color="primary"
                    shape="rounded"
                  />
                </Box>
              )}
            </Paper>
          </motion.div>

          {/* Summary */}
          {transactions && transactions.length > 0 && (
            <motion.div variants={itemVariants}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                  <Card
                    sx={{
                      height: "100%",
                      border: `1px solid ${theme.palette.divider}`,
                      boxShadow: "none",
                    }}
                  >
                    <CardContent>
                      <Typography variant="h6" fontWeight={600} gutterBottom>
                        Transaction Summary
                      </Typography>
                      <Divider sx={{ my: 2 }} />
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          mb: 1,
                        }}
                      >
                        <Typography variant="body2" color="text.secondary">
                          Total Transactions
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {transactions.length}
                        </Typography>
                      </Box>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          mb: 1,
                        }}
                      >
                        <Typography variant="body2" color="text.secondary">
                          Send Transactions
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {
                            transactions.filter((tx) => tx.type === "send")
                              .length
                          }
                        </Typography>
                      </Box>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          mb: 1,
                        }}
                      >
                        <Typography variant="body2" color="text.secondary">
                          Receive Transactions
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {
                            transactions.filter((tx) => tx.type === "receive")
                              .length
                          }
                        </Typography>
                      </Box>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          mb: 1,
                        }}
                      >
                        <Typography variant="body2" color="text.secondary">
                          Swap Transactions
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {
                            transactions.filter((tx) => tx.type === "swap")
                              .length
                          }
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Card
                    sx={{
                      height: "100%",
                      border: `1px solid ${theme.palette.divider}`,
                      boxShadow: "none",
                    }}
                  >
                    <CardContent>
                      <Typography variant="h6" fontWeight={600} gutterBottom>
                        Network Distribution
                      </Typography>
                      <Divider sx={{ my: 2 }} />
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          mb: 1,
                        }}
                      >
                        <Typography variant="body2" color="text.secondary">
                          Ethereum
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {
                            transactions.filter(
                              (tx) => tx.network === "Ethereum",
                            ).length
                          }
                        </Typography>
                      </Box>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          mb: 1,
                        }}
                      >
                        <Typography variant="body2" color="text.secondary">
                          Polygon
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {
                            transactions.filter(
                              (tx) => tx.network === "Polygon",
                            ).length
                          }
                        </Typography>
                      </Box>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          mb: 1,
                        }}
                      >
                        <Typography variant="body2" color="text.secondary">
                          Bitcoin
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          {
                            transactions.filter(
                              (tx) => tx.network === "Bitcoin",
                            ).length
                          }
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Card
                    sx={{
                      height: "100%",
                      border: `1px solid ${theme.palette.divider}`,
                      boxShadow: "none",
                    }}
                  >
                    <CardContent>
                      <Typography variant="h6" fontWeight={600} gutterBottom>
                        Fee Summary
                      </Typography>
                      <Divider sx={{ my: 2 }} />
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          mb: 1,
                        }}
                      >
                        <Typography variant="body2" color="text.secondary">
                          Total Fees Paid
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          $
                          {transactions
                            .reduce(
                              (sum, tx) =>
                                sum + parseFloat(tx.fee?.replace("$", "") || 0),
                              0,
                            )
                            .toFixed(2)}
                        </Typography>
                      </Box>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          mb: 1,
                        }}
                      >
                        <Typography variant="body2" color="text.secondary">
                          Average Fee
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          $
                          {(
                            transactions.reduce(
                              (sum, tx) =>
                                sum + parseFloat(tx.fee?.replace("$", "") || 0),
                              0,
                            ) / transactions.length
                          ).toFixed(2)}
                        </Typography>
                      </Box>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          mb: 1,
                        }}
                      >
                        <Typography variant="body2" color="text.secondary">
                          Highest Fee
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          $
                          {Math.max(
                            ...transactions.map((tx) =>
                              parseFloat(tx.fee?.replace("$", "") || 0),
                            ),
                          ).toFixed(2)}
                        </Typography>
                      </Box>
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "space-between",
                          mb: 1,
                        }}
                      >
                        <Typography variant="body2" color="text.secondary">
                          Lowest Fee
                        </Typography>
                        <Typography variant="body2" fontWeight={500}>
                          $
                          {Math.min(
                            ...transactions
                              .filter(
                                (tx) =>
                                  parseFloat(tx.fee?.replace("$", "") || 0) > 0,
                              )
                              .map((tx) =>
                                parseFloat(tx.fee?.replace("$", "") || 0),
                              ),
                          ).toFixed(2)}
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </motion.div>
          )}
        </motion.div>
      </Container>
    </Box>
  );
};

export default Transactions;
