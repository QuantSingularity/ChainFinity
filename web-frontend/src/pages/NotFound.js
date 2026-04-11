import { Box, Button, Container, Typography } from "@mui/material";
import { styled } from "@mui/material/styles";
import { motion } from "framer-motion";
import { Link as RouterLink } from "react-router-dom";

const NotFoundContainer = styled(Box)(({ theme }) => ({
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "center",
  minHeight: "calc(100vh - 200px)",
  textAlign: "center",
  padding: theme.spacing(3),
}));

const NotFoundImage = styled("img")(({ theme }) => ({
  maxWidth: "100%",
  height: "auto",
  marginBottom: theme.spacing(4),
}));

const NotFound = () => {
  return (
    <Container maxWidth="md">
      <NotFoundContainer>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <NotFoundImage
            src="/404-illustration.svg"
            alt="Page Not Found"
            sx={{ maxWidth: 400 }}
          />

          <Typography
            variant="h2"
            component="h1"
            fontWeight={700}
            gutterBottom
            sx={{
              background: "linear-gradient(45deg, #3a36e0 0%, #6c63ff 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            404
          </Typography>

          <Typography variant="h4" fontWeight={600} gutterBottom>
            Page Not Found
          </Typography>

          <Typography
            variant="body1"
            color="text.secondary"
            paragraph
            sx={{ maxWidth: 600, mx: "auto" }}
          >
            The page you are looking for might have been removed, had its name
            changed, or is temporarily unavailable.
          </Typography>

          <Button
            variant="contained"
            color="primary"
            size="large"
            component={RouterLink}
            to="/"
            sx={{ mt: 2 }}
          >
            Back to Home
          </Button>
        </motion.div>
      </NotFoundContainer>
    </Container>
  );
};

export default NotFound;
