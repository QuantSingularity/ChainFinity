import { Box, Container, Grid, Link, Typography } from "@mui/material";

function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <Box
      component="footer"
      sx={{
        py: 3,
        px: 2,
        mt: "auto",
        backgroundColor: (theme) =>
          theme.palette.mode === "light"
            ? theme.palette.grey[200]
            : theme.palette.grey[800],
      }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={4}>
          <Grid item xs={12} sm={4}>
            <Typography variant="h6" color="text.primary" gutterBottom>
              ChainFinity
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Empowering decentralized finance with AI-driven insights.
            </Typography>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography variant="h6" color="text.primary" gutterBottom>
              Quick Links
            </Typography>
            <Box component="ul" sx={{ listStyle: "none", p: 0, m: 0 }}>
              <li>
                <Link href="/" color="inherit" underline="hover">
                  Home
                </Link>
              </li>
              <li>
                <Link href="/dashboard" color="inherit" underline="hover">
                  Dashboard
                </Link>
              </li>
              <li>
                <Link href="/docs" color="inherit" underline="hover">
                  Documentation
                </Link>
              </li>
            </Box>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography variant="h6" color="text.primary" gutterBottom>
              Contact
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Email: support@chainfinity.com
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Discord: discord.gg/chainfinity
            </Typography>
          </Grid>
        </Grid>
        <Box mt={3}>
          <Typography variant="body2" color="text.secondary" align="center">
            © {currentYear} ChainFinity. All rights reserved.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}

export default Footer;
