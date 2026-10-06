import Refresh from "@mui/icons-material/Refresh";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  FormControl,
  Grid,
  InputLabel,
  List,
  ListItem,
  ListItemText,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useRiskInsights } from "../hooks/useRiskInsights";

export const BUCKET_COLORS = {
  low: "success",
  medium: "info",
  high: "warning",
  extreme: "error",
};

export const formatPercent = (value, digits = 1) =>
  typeof value === "number" && Number.isFinite(value)
    ? `${(value * 100).toFixed(digits)}%`
    : "n/a";

export const correlationColor = (value) => {
  const clamped = Math.max(-1, Math.min(1, Number(value) || 0));
  const alpha = Math.abs(clamped) * 0.6;
  return clamped >= 0
    ? `rgba(239, 68, 68, ${alpha})`
    : `rgba(56, 189, 248, ${alpha})`;
};

const MODEL_LABELS = {
  volatility: "Volatility",
  correlation: "Correlation",
  exploit: "Exploit",
  liquidity: "Liquidity",
  smart_money: "Smart money",
};

const ModelStatus = ({ status }) => {
  if (!status) return null;
  return (
    <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
      {Object.entries(status.models || {}).map(([name, info]) => (
        <Chip
          key={name}
          size="small"
          label={`${MODEL_LABELS[name] || name}: ${info.mode.replace("_", " ")}`}
          color={info.mode === "trained" ? "success" : "default"}
          variant={info.mode === "trained" ? "filled" : "outlined"}
        />
      ))}
    </Box>
  );
};

const VolatilityCard = ({ symbol, forecast }) => (
  <Card variant="outlined" sx={{ height: "100%" }}>
    <CardContent>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
        <Typography variant="h6">{symbol}</Typography>
        <Chip
          size="small"
          label={forecast.vol_bucket}
          color={BUCKET_COLORS[forecast.vol_bucket] || "default"}
        />
      </Box>
      <Typography variant="h4">
        {formatPercent(forecast.predicted_vol)}
      </Typography>
      <Typography variant="body2" color="text.secondary">
        Forecast annualised volatility, {forecast.forecast_horizon_days}d
        horizon
      </Typography>
      {forecast.confidence_interval && (
        <Typography variant="body2" sx={{ mt: 1 }}>
          90% range: {formatPercent(forecast.confidence_interval[0])} to{" "}
          {formatPercent(forecast.confidence_interval[1])}
        </Typography>
      )}
      <Typography variant="body2" color="text.secondary">
        Recent realised: {formatPercent(forecast.recent_realized_vol)}
      </Typography>
      <Typography variant="caption" color="text.secondary">
        Model: {forecast.model.replace("_", " ")}
      </Typography>
    </CardContent>
  </Card>
);

const CorrelationTable = ({ correlation }) => (
  <TableContainer component={Paper} variant="outlined">
    <Table size="small" aria-label="correlation matrix">
      <TableHead>
        <TableRow>
          <TableCell />
          {correlation.assets.map((asset) => (
            <TableCell key={asset} align="center">
              {asset}
            </TableCell>
          ))}
        </TableRow>
      </TableHead>
      <TableBody>
        {correlation.assets.map((rowAsset, i) => (
          <TableRow key={rowAsset}>
            <TableCell component="th" scope="row">
              {rowAsset}
            </TableCell>
            {correlation.matrix[i].map((value, j) => (
              <TableCell
                key={`${rowAsset}-${correlation.assets[j]}`}
                align="center"
                sx={{ backgroundColor: correlationColor(value) }}
              >
                {value.toFixed(2)}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </TableContainer>
);

const AssessmentPanel = ({ assessment, onRun, running }) => (
  <Card variant="outlined">
    <CardContent>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 2,
        }}
      >
        <Typography variant="h6">Risk assessment</Typography>
        <Button variant="contained" onClick={onRun} disabled={running}>
          {running ? "Running..." : "Run assessment"}
        </Button>
      </Box>
      {!assessment && (
        <Typography color="text.secondary">
          No assessment yet for this portfolio.
        </Typography>
      )}
      {assessment && (
        <>
          <Box sx={{ display: "flex", gap: 2, alignItems: "center", mb: 2 }}>
            <Typography variant="h3" component="span">
              {Number(assessment.risk_score).toFixed(1)}
            </Typography>
            <Chip label={assessment.risk_level} color="primary" />
            {assessment.risk_grade && (
              <Chip label={assessment.risk_grade} variant="outlined" />
            )}
            {assessment.action_required && (
              <Chip label="Action required" color="error" />
            )}
          </Box>
          {assessment.recommendations?.length > 0 && (
            <List dense>
              {assessment.recommendations.map((text) => (
                <ListItem key={text} disableGutters>
                  <ListItemText primary={text} />
                </ListItem>
              ))}
            </List>
          )}
          {assessment.stress_tests?.length > 0 && (
            <TableContainer sx={{ mt: 2 }}>
              <Table size="small" aria-label="stress tests">
                <TableHead>
                  <TableRow>
                    <TableCell>Scenario</TableCell>
                    <TableCell align="right">Potential loss</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {assessment.stress_tests
                    .filter((t) => t.status === "completed")
                    .map((test) => (
                      <TableRow key={test.scenario_name}>
                        <TableCell>{test.scenario_name}</TableCell>
                        <TableCell align="right">
                          {Number(test.potential_loss_percent).toFixed(1)}%
                        </TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </>
      )}
    </CardContent>
  </Card>
);

const RiskInsights = () => {
  const {
    portfolios,
    portfolioId,
    aiStatus,
    insights,
    assessment,
    loading,
    assessing,
    error,
    selectPortfolio,
    refresh,
    runAssessment,
  } = useRiskInsights();

  const volatility = insights ? Object.entries(insights.volatility || {}) : [];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 2,
          mb: 3,
        }}
      >
        <Typography variant="h4" component="h1">
          Risk Intelligence
        </Typography>
        <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
          {portfolios.length > 0 && (
            <FormControl size="small" sx={{ minWidth: 220 }}>
              <InputLabel id="risk-portfolio-label">Portfolio</InputLabel>
              <Select
                labelId="risk-portfolio-label"
                label="Portfolio"
                value={portfolioId}
                onChange={(event) => selectPortfolio(event.target.value)}
              >
                {portfolios.map((portfolio) => (
                  <MenuItem key={portfolio.id} value={portfolio.id}>
                    {portfolio.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          <Button
            startIcon={<Refresh />}
            onClick={refresh}
            disabled={loading || !portfolioId}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      <ModelStatus status={aiStatus} />

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error.message}
        </Alert>
      )}

      {loading && (
        <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
          <CircularProgress aria-label="loading risk insights" />
        </Box>
      )}

      {!loading && portfolios.length === 0 && !error && (
        <Alert severity="info" sx={{ mt: 3 }}>
          Create a portfolio with assets to see risk analytics.
        </Alert>
      )}

      {!loading && insights && (
        <Box sx={{ mt: 3 }}>
          {insights.warnings?.map((warning) => (
            <Alert key={warning} severity="warning" sx={{ mb: 1 }}>
              {warning}
            </Alert>
          ))}

          <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>
            Volatility forecast
          </Typography>
          <Grid container spacing={2}>
            {volatility.map(([symbol, forecast]) => (
              <Grid item xs={12} sm={6} md={4} key={symbol}>
                <VolatilityCard symbol={symbol} forecast={forecast} />
              </Grid>
            ))}
          </Grid>

          {insights.correlation && (
            <Box sx={{ mt: 4 }}>
              <Typography variant="h6" sx={{ mb: 1 }}>
                Predicted correlations
              </Typography>
              <CorrelationTable correlation={insights.correlation} />
              <Typography variant="caption" color="text.secondary">
                Model: {insights.correlation.model.replace("_", " ")}
              </Typography>
            </Box>
          )}
        </Box>
      )}

      {portfolioId && !loading && (
        <Box sx={{ mt: 4 }}>
          <AssessmentPanel
            assessment={assessment}
            onRun={runAssessment}
            running={assessing}
          />
        </Box>
      )}
    </Container>
  );
};

export default RiskInsights;
