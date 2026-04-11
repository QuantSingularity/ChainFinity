import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { useRouter, usePathname } from "next/navigation";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { useApp } from "@/context/AppContext";

jest.mock("next/navigation", () => ({
  useRouter: jest.fn(),
  usePathname: jest.fn(),
}));

jest.mock("@/context/AppContext", () => ({
  useApp: jest.fn(),
}));

const mockActions = {
  login: jest.fn(),
  logout: jest.fn(),
  register: jest.fn(),
  clearError: jest.fn(),
  toggleTheme: jest.fn(),
  connectWallet: jest.fn(),
  disconnectWallet: jest.fn(),
};

const defaultAppState = {
  user: null,
  isAuthenticated: false,
  loading: false,
  error: null,
  darkMode: false,
  wallet: { isConnected: false, address: null, balance: null, network: null },
  actions: mockActions,
};

describe("Navbar", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({ push: jest.fn() });
    (usePathname as jest.Mock).mockReturnValue("/");
    (useApp as jest.Mock).mockReturnValue(defaultAppState);
  });

  it("renders the brand name", () => {
    render(<Navbar />);
    expect(screen.getAllByText("ChainFinity").length).toBeGreaterThan(0);
  });

  it("shows Login button when unauthenticated", () => {
    render(<Navbar />);
    expect(screen.getByRole("link", { name: /login/i })).toBeInTheDocument();
  });

  it("shows Connect Wallet button when wallet is not connected", () => {
    render(<Navbar />);
    expect(
      screen.getByRole("button", { name: /connect wallet/i }),
    ).toBeInTheDocument();
  });

  it("shows Logout button when user is logged in", () => {
    (useApp as jest.Mock).mockReturnValue({
      ...defaultAppState,
      user: { id: "1", username: "testuser", email: "test@example.com" },
      isAuthenticated: true,
    });
    render(<Navbar />);
    expect(screen.getByRole("button", { name: /logout/i })).toBeInTheDocument();
  });

  it("shows truncated wallet address when wallet is connected", () => {
    (useApp as jest.Mock).mockReturnValue({
      ...defaultAppState,
      wallet: {
        isConnected: true,
        address: "0x1234567890abcdef1234567890abcdef12345678",
        balance: "1.0000 ETH",
        network: "Ethereum Mainnet",
      },
    });
    render(<Navbar />);
    expect(screen.getByText(/0x1234/)).toBeInTheDocument();
  });

  it("calls connectWallet action when Connect Wallet is clicked", async () => {
    render(<Navbar />);
    const btn = screen.getByRole("button", { name: /connect wallet/i });
    fireEvent.click(btn);
    await waitFor(() => expect(mockActions.connectWallet).toHaveBeenCalled());
  });

  it("calls disconnectWallet when wallet address button is clicked", async () => {
    (useApp as jest.Mock).mockReturnValue({
      ...defaultAppState,
      wallet: {
        isConnected: true,
        address: "0xabc123def456abc123def456abc123def456abc1",
        balance: "2.5000 ETH",
        network: "Ethereum Mainnet",
      },
    });
    render(<Navbar />);
    const btn = screen.getByRole("button", { name: /0xabc1/i });
    fireEvent.click(btn);
    await waitFor(() =>
      expect(mockActions.disconnectWallet).toHaveBeenCalled(),
    );
  });

  it("calls logout when Logout is clicked", async () => {
    (useApp as jest.Mock).mockReturnValue({
      ...defaultAppState,
      user: { id: "1", username: "testuser", email: "test@example.com" },
      isAuthenticated: true,
    });
    render(<Navbar />);
    const btn = screen.getByRole("button", { name: /logout/i });
    fireEvent.click(btn);
    await waitFor(() => expect(mockActions.logout).toHaveBeenCalled());
  });

  it("toggles theme when ModeToggle is clicked", async () => {
    render(<Navbar />);
    const toggleBtn = screen.getByRole("button", { name: /toggle theme/i });
    fireEvent.click(toggleBtn);
    await waitFor(() => expect(mockActions.toggleTheme).toHaveBeenCalled());
  });
});

describe("Footer", () => {
  it("renders brand name", () => {
    render(<Footer />);
    expect(screen.getByText("ChainFinity")).toBeInTheDocument();
  });

  it("renders current year in copyright", () => {
    render(<Footer />);
    const year = new Date().getFullYear().toString();
    expect(screen.getByText(new RegExp(year))).toBeInTheDocument();
  });

  it("renders quick links", () => {
    render(<Footer />);
    expect(screen.getByRole("link", { name: /home/i })).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /dashboard/i }),
    ).toBeInTheDocument();
  });

  it("renders social links", () => {
    render(<Footer />);
    const githubLink = screen.getByRole("link", { name: /github/i });
    expect(githubLink).toBeInTheDocument();
    expect(githubLink).toHaveAttribute("href");
  });
});
