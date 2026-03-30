import {
  GitHub as GitHubIcon,
  LinkedIn as LinkedInIcon,
  Telegram as TelegramIcon,
  Twitter as TwitterIcon,
} from "@mui/icons-material";
import {
  Box,
  Container,
  Divider,
  Grid,
  IconButton,
  Link,
  Typography,
  useTheme,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { motion } from "framer-motion";

const FooterContainer = styled(Box)(({ theme }) => ({
  backgroundColor:
    theme.palette.mode === "light"
      ? "rgba(248, 249, 252, 0.8)"
      : "rgba(18, 18, 18, 0.8)",
  backdropFilter: "blur(8px)",
  borderTop: `1px solid ${theme.palette.divider}`,
  paddingTop: theme.spacing(6),
  paddingBottom: theme.spacing(6),
  [theme.breakpoints.down("sm")]: {
    paddingTop: theme.spacing(4),
    paddingBottom: theme.spacing(4),
  },
}));

const FooterLink = styled(Link)(({ theme }) => ({
  color: theme.palette.text.secondary,
  textDecoration: "none",
  "&:hover": {
    color: theme.palette.primary.main,
    textDecoration: "none",
  },
  transition: "color 0.2s ease-in-out",
}));

const SocialIcon = styled(IconButton)(({ theme }) => ({
  color: theme.palette.text.secondary,
  "&:hover": {
    color: theme.palette.primary.main,
    backgroundColor:
      theme.palette.mode === "light"
        ? "rgba(58, 54, 224, 0.08)"
        : "rgba(108, 99, 255, 0.08)",
  },
}));

const Footer = () => {
  const _theme = useTheme();
  const currentYear = new Date().getFullYear();

  return (
    <FooterContainer
      component={motion.footer}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.2, duration: 0.5 }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={4}>
          <Grid item xs={12} sm={6} md={3}>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 700,
                mb: 2,
                background: "linear-gradient(45deg, #3a36e0 0%, #6c63ff 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              ChainFinity
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Advanced blockchain portfolio tracker and DeFi analytics platform.
            </Typography>
            <Box sx={{ display: "flex", gap: 1 }}>
              <SocialIcon size="small" aria-label="github">
                <GitHubIcon fontSize="small" />
              </SocialIcon>
              <SocialIcon size="small" aria-label="twitter">
                <TwitterIcon fontSize="small" />
              </SocialIcon>
              <SocialIcon size="small" aria-label="linkedin">
                <LinkedInIcon fontSize="small" />
              </SocialIcon>
              <SocialIcon size="small" aria-label="telegram">
                <TelegramIcon fontSize="small" />
              </SocialIcon>
            </Box>
          </Grid>

          <Grid item xs={6} sm={6} md={3}>
            <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 2 }}>
              Product
            </Typography>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              <FooterLink href="#">Features</FooterLink>
              <FooterLink href="#">Pricing</FooterLink>
              <FooterLink href="#">Roadmap</FooterLink>
              <FooterLink href="#">Changelog</FooterLink>
            </Box>
          </Grid>

          <Grid item xs={6} sm={6} md={3}>
            <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 2 }}>
              Resources
            </Typography>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              <FooterLink href="#">Documentation</FooterLink>
              <FooterLink href="#">API Reference</FooterLink>
              <FooterLink href="#">Tutorials</FooterLink>
              <FooterLink href="#">Blog</FooterLink>
            </Box>
          </Grid>

          <Grid item xs={6} sm={6} md={3}>
            <Typography variant="subtitle1" fontWeight={600} sx={{ mb: 2 }}>
              Company
            </Typography>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              <FooterLink href="#">About</FooterLink>
              <FooterLink href="#">Careers</FooterLink>
              <FooterLink href="#">Privacy Policy</FooterLink>
              <FooterLink href="#">Terms of Service</FooterLink>
            </Box>
          </Grid>
        </Grid>

        <Divider sx={{ my: 4 }} />

        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 2,
          }}
        >
          <Typography variant="body2" color="text.secondary">
            © {currentYear} ChainFinity. All rights reserved.
          </Typography>
          <Box sx={{ display: "flex", gap: 3 }}>
            <FooterLink href="#" variant="body2">
              Privacy
            </FooterLink>
            <FooterLink href="#" variant="body2">
              Terms
            </FooterLink>
            <FooterLink href="#" variant="body2">
              Cookies
            </FooterLink>
          </Box>
        </Box>
      </Container>
    </FooterContainer>
  );
};

export default Footer;
