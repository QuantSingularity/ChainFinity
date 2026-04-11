"use client";

import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useApp } from "@/context/AppContext";

export function ModeToggle() {
  const { darkMode, actions } = useApp();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={actions.toggleTheme}
      aria-label="Toggle theme"
    >
      {darkMode ? (
        <Sun className="h-4 w-4 transition-transform duration-300 rotate-0 scale-100" />
      ) : (
        <Moon className="h-4 w-4 transition-transform duration-300 rotate-0 scale-100" />
      )}
      <span className="sr-only">Toggle theme</span>
    </Button>
  );
}
