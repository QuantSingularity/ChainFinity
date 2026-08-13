import { createTheme, ThemeProvider } from "@mui/material/styles";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import CreateProposal from "../../components/governance/CreateProposal";
import { blockchainAPI } from "../../services/api";

jest.mock("../../services/api", () => ({
  blockchainAPI: {
    getDeployedContracts: jest.fn(),
  },
}));

const renderWithTheme = (ui) => {
  const theme = createTheme();
  return render(<ThemeProvider theme={theme}>{ui}</ThemeProvider>);
};

const VAULT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa";

describe("CreateProposal", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("shows validation errors and does not submit when required fields are empty", async () => {
    const onSubmit = jest.fn();
    blockchainAPI.getDeployedContracts.mockResolvedValue({
      data: { connected: true, chain_id: 31337, contracts: [] },
    });
    const user = userEvent.setup();
    renderWithTheme(<CreateProposal onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: /submit proposal/i }));

    expect(await screen.findByText("Title is required")).toBeInTheDocument();
    expect(screen.getByText("Description is required")).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  test("rejects an invalid target address", async () => {
    const onSubmit = jest.fn();
    blockchainAPI.getDeployedContracts.mockResolvedValue({
      data: { connected: true, chain_id: 31337, contracts: [] },
    });
    const user = userEvent.setup();
    renderWithTheme(<CreateProposal onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/proposal title/i), "Title");
    await user.type(screen.getByLabelText(/description/i), "Description");
    await user.type(
      screen.getByLabelText(/target contract address/i),
      "not-an-address",
    );
    await user.click(screen.getByRole("button", { name: /submit proposal/i }));

    expect(
      await screen.findByText(/enter a valid ethereum address/i),
    ).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  test("offers ChainFinity's own deployed contracts and fills the address on selection", async () => {
    blockchainAPI.getDeployedContracts.mockResolvedValue({
      data: {
        connected: true,
        chain_id: 31337,
        contracts: [
          { name: "AssetVault", address: VAULT_ADDRESS, has_abi: true },
        ],
      },
    });
    const user = userEvent.setup();
    renderWithTheme(<CreateProposal onSubmit={jest.fn()} />);

    const field = screen.getByLabelText(/target contract address/i);
    await user.click(field);
    await user.type(field, "AssetVault");

    const option = await screen.findByText("AssetVault");
    await user.click(option);

    expect(field).toHaveValue(VAULT_ADDRESS);
  });

  test("submits a valid proposal and resets the form", async () => {
    blockchainAPI.getDeployedContracts.mockResolvedValue({
      data: { connected: true, chain_id: 31337, contracts: [] },
    });
    const onSubmit = jest.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    renderWithTheme(<CreateProposal onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/proposal title/i), "Add pool");
    await user.type(
      screen.getByLabelText(/description/i),
      "Add a new staking pool.",
    );
    await user.click(screen.getByRole("button", { name: /submit proposal/i }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ title: "Add pool" }),
    );
    expect(screen.getByLabelText(/proposal title/i)).toHaveValue("");
  });

  test("degrades to a plain text field when the backend is unreachable", async () => {
    blockchainAPI.getDeployedContracts.mockRejectedValue(
      new Error("network error"),
    );
    renderWithTheme(<CreateProposal onSubmit={jest.fn()} />);

    // No crash, and the field is still usable as free text.
    expect(
      await screen.findByLabelText(/target contract address/i),
    ).toBeInTheDocument();
  });
});
