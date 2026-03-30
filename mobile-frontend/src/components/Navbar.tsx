"use client";

import { LogIn, LogOut, Menu, Wallet } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ModeToggle } from "@/components/layout/mode-toggle"; // Assuming this exists for dark/light mode
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { useApp } from "../context/AppContext"; // Assuming context remains compatible
import { formatAddress } from "../utils/helpers"; // Assuming helper remains compatible

function Navbar() {
  const pathname = usePathname();
  const { state, actions } = useApp();
  const { wallet, user } = state;

  const navItems = [
    { label: "Home", path: "/" },
    { label: "Dashboard", path: "/dashboard" },
    // Add more relevant nav items for ChainFinity if needed
  ];

  const NavLinks = ({ isMobile = false }: { isMobile?: boolean }) => (
    <nav
      className={`flex ${isMobile ? "flex-col space-y-2 mt-4" : "items-center space-x-4 lg:space-x-6"}`}
    >
      {navItems.map((item) => (
        <Link
          key={item.path}
          href={item.path}
          className={`text-sm font-medium transition-colors hover:text-primary ${pathname === item.path ? "text-primary" : "text-muted-foreground"}`}
        >
          {item.label}
        </Link>
      ))}
    </nav>
  );

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 max-w-screen-2xl items-center">
        {/* Logo/Brand Name */}
        <Link href="/" className="mr-6 flex items-center space-x-2">
          {/* <Icons.logo className="h-6 w-6" /> Optional Logo Icon */}
          <span className="font-bold inline-block bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-cyan-500 dark:from-indigo-400 dark:to-cyan-400">
            ChainFinity
          </span>
        </Link>

        {/* Desktop Navigation */}
        <div className="hidden md:flex flex-1">
          <NavLinks />
        </div>

        {/* Right Side Actions (Desktop) */}
        <div className="hidden md:flex flex-1 items-center justify-end space-x-3">
          {wallet.isConnected ? (
            <Button
              variant="outline"
              size="sm"
              onClick={actions.disconnectWallet}
            >
              <Wallet className="h-4 w-4 mr-2" />
              {formatAddress(wallet.address)}
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

        {/* Mobile Navigation Trigger */}
        <div className="md:hidden flex flex-1 justify-end">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Toggle Menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[300px] sm:w-[400px]">
              <div className="flex flex-col p-4 space-y-4">
                <Link href="/" className="mb-4">
                  <span className="font-bold text-lg bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-cyan-500 dark:from-indigo-400 dark:to-cyan-400">
                    ChainFinity
                  </span>
                </Link>
                <NavLinks isMobile={true} />
                <hr className="my-4" />
                <div className="flex flex-col space-y-3">
                  {wallet.isConnected ? (
                    <Button
                      variant="outline"
                      onClick={actions.disconnectWallet}
                    >
                      <Wallet className="h-4 w-4 mr-2" />
                      {formatAddress(wallet.address)}
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
                  <ModeToggle />
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
