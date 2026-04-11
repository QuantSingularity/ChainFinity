"use client";

import { LogIn, LogOut, Menu, Wallet, Settings, History } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ModeToggle } from "@/components/layout/mode-toggle";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { useApp } from "@/context/AppContext";
import { formatAddress } from "@/utils/helpers";

function Navbar() {
  const pathname = usePathname();
  const { wallet, user, actions } = useApp();

  const navItems = [
    { label: "Home", path: "/" },
    { label: "Dashboard", path: "/dashboard" },
    { label: "Transactions", path: "/transactions" },
    { label: "Settings", path: "/settings" },
  ];

  const NavLinks = ({ isMobile = false }: { isMobile?: boolean }) => (
    <nav
      className={`flex ${
        isMobile
          ? "flex-col space-y-1 mt-4"
          : "items-center space-x-4 lg:space-x-6"
      }`}
    >
      {navItems.map((item) => (
        <Link
          key={item.path}
          href={item.path}
          className={`text-sm font-medium transition-colors hover:text-primary ${
            pathname === item.path ? "text-primary" : "text-muted-foreground"
          } ${isMobile ? "flex items-center gap-2 px-2 py-2 rounded-md hover:bg-muted" : ""}`}
        >
          {isMobile && item.path === "/settings" && (
            <Settings className="h-4 w-4" />
          )}
          {isMobile && item.path === "/transactions" && (
            <History className="h-4 w-4" />
          )}
          {item.label}
        </Link>
      ))}
    </nav>
  );

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 max-w-screen-2xl items-center">
        <Link href="/" className="mr-6 flex items-center space-x-2">
          <span className="font-bold inline-block bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-cyan-500 dark:from-indigo-400 dark:to-cyan-400">
            ChainFinity
          </span>
        </Link>

        <div className="hidden md:flex flex-1">
          <NavLinks />
        </div>

        <div className="hidden md:flex flex-1 items-center justify-end space-x-3">
          {wallet.isConnected ? (
            <Button
              variant="outline"
              size="sm"
              onClick={actions.disconnectWallet}
            >
              <Wallet className="h-4 w-4 mr-2" />
              {formatAddress(wallet.address ?? "")}
            </Button>
          ) : (
            <Button size="sm" onClick={actions.connectWallet}>
              <Wallet className="h-4 w-4 mr-2" />
              Connect Wallet
            </Button>
          )}

          {user ? (
            <Button variant="ghost" size="sm" onClick={actions.logout}>
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          ) : (
            <Button variant="ghost" size="sm" asChild>
              <Link href="/login">
                <LogIn className="h-4 w-4 mr-2" />
                Login
              </Link>
            </Button>
          )}
          <ModeToggle />
        </div>

        <div className="md:hidden flex flex-1 justify-end">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Toggle Menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[300px] sm:w-[360px]">
              <div className="flex flex-col p-4 space-y-4">
                <Link href="/" className="mb-2">
                  <span className="font-bold text-lg bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-cyan-500 dark:from-indigo-400 dark:to-cyan-400">
                    ChainFinity
                  </span>
                </Link>
                <NavLinks isMobile />
                <hr className="border-border/40" />
                <div className="flex flex-col space-y-2">
                  {wallet.isConnected ? (
                    <Button
                      variant="outline"
                      onClick={actions.disconnectWallet}
                    >
                      <Wallet className="h-4 w-4 mr-2" />
                      {formatAddress(wallet.address ?? "")}
                    </Button>
                  ) : (
                    <Button onClick={actions.connectWallet}>
                      <Wallet className="h-4 w-4 mr-2" />
                      Connect Wallet
                    </Button>
                  )}
                  {user ? (
                    <Button variant="ghost" onClick={actions.logout}>
                      <LogOut className="h-4 w-4 mr-2" />
                      Logout
                    </Button>
                  ) : (
                    <Button variant="ghost" asChild>
                      <Link href="/login">
                        <LogIn className="h-4 w-4 mr-2" />
                        Login
                      </Link>
                    </Button>
                  )}
                  <div className="flex items-center justify-between px-2 py-1">
                    <span className="text-sm text-muted-foreground">Theme</span>
                    <ModeToggle />
                  </div>
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}

export default Navbar;
