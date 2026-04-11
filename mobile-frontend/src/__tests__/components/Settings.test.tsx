import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import SettingsPage from "@/app/settings/page";
import { useAuth } from "@/hooks/useAuth";

jest.mock("@/hooks/useAuth", () => ({
  useAuth: jest.fn(),
}));

const mockUpdatePassword = jest.fn();

beforeEach(() => {
  jest.clearAllMocks();
  (useAuth as jest.Mock).mockReturnValue({
    updatePassword: mockUpdatePassword,
    loading: false,
    error: null,
  });
});

describe("SettingsPage", () => {
  it("renders Settings heading", () => {
    render(<SettingsPage />);
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("renders Change Password section", () => {
    render(<SettingsPage />);
    expect(screen.getByText("Change Password")).toBeInTheDocument();
  });

  it("renders Notification Preferences section", () => {
    render(<SettingsPage />);
    expect(screen.getByText("Notification Preferences")).toBeInTheDocument();
  });

  it("shows error if passwords do not match", async () => {
    render(<SettingsPage />);
    fireEvent.change(screen.getByLabelText(/current password/i), {
      target: { value: "oldpass123" },
    });
    fireEvent.change(screen.getByLabelText(/^new password$/i), {
      target: { value: "newpass123" },
    });
    fireEvent.change(screen.getByLabelText(/confirm new password/i), {
      target: { value: "different123" },
    });
    fireEvent.submit(
      screen.getByRole("button", { name: /update password/i }).closest("form")!,
    );
    await waitFor(() =>
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument(),
    );
  });

  it("shows error if new password is too short", async () => {
    render(<SettingsPage />);
    fireEvent.change(screen.getByLabelText(/current password/i), {
      target: { value: "oldpass123" },
    });
    fireEvent.change(screen.getByLabelText(/^new password$/i), {
      target: { value: "short" },
    });
    fireEvent.change(screen.getByLabelText(/confirm new password/i), {
      target: { value: "short" },
    });
    fireEvent.submit(
      screen.getByRole("button", { name: /update password/i }).closest("form")!,
    );
    await waitFor(() =>
      expect(screen.getByText(/at least 8 characters/i)).toBeInTheDocument(),
    );
  });

  it("calls updatePassword on valid submit", async () => {
    mockUpdatePassword.mockResolvedValue(true);
    render(<SettingsPage />);
    fireEvent.change(screen.getByLabelText(/current password/i), {
      target: { value: "oldpass123" },
    });
    fireEvent.change(screen.getByLabelText(/^new password$/i), {
      target: { value: "newpass123" },
    });
    fireEvent.change(screen.getByLabelText(/confirm new password/i), {
      target: { value: "newpass123" },
    });
    fireEvent.submit(
      screen.getByRole("button", { name: /update password/i }).closest("form")!,
    );
    await waitFor(() =>
      expect(mockUpdatePassword).toHaveBeenCalledWith({
        currentPassword: "oldpass123",
        newPassword: "newpass123",
      }),
    );
  });

  it("shows success message after successful password update", async () => {
    mockUpdatePassword.mockResolvedValue(true);
    render(<SettingsPage />);
    fireEvent.change(screen.getByLabelText(/current password/i), {
      target: { value: "oldpass123" },
    });
    fireEvent.change(screen.getByLabelText(/^new password$/i), {
      target: { value: "newpass123" },
    });
    fireEvent.change(screen.getByLabelText(/confirm new password/i), {
      target: { value: "newpass123" },
    });
    fireEvent.submit(
      screen.getByRole("button", { name: /update password/i }).closest("form")!,
    );
    await waitFor(() =>
      expect(
        screen.getByText(/password updated successfully/i),
      ).toBeInTheDocument(),
    );
  });

  it("shows auth error from hook", () => {
    (useAuth as jest.Mock).mockReturnValue({
      updatePassword: mockUpdatePassword,
      loading: false,
      error: "Invalid current password",
    });
    render(<SettingsPage />);
    expect(screen.getByText("Invalid current password")).toBeInTheDocument();
  });

  it("toggles email notification switch", () => {
    render(<SettingsPage />);
    const switches = screen.getAllByRole("switch");
    const emailSwitch = switches[0];
    expect(emailSwitch).toBeChecked();
    fireEvent.click(emailSwitch);
    expect(emailSwitch).not.toBeChecked();
  });
});
