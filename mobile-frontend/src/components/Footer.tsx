import { Github, Mail, Twitter } from "lucide-react"; // Example icons
import Link from "next/link";
import { Separator } from "@/components/ui/separator";

function Footer() {
  const currentYear = new Date().getFullYear();

  const quickLinks = [
    { label: "Home", path: "/" },
    { label: "Dashboard", path: "/dashboard" },
    { label: "Documentation", path: "/docs" }, // Assuming a docs page
  ];

  const socialLinks = [
    { label: "GitHub", icon: Github, url: "https://github.com/your-repo" }, // Replace with actual URL
    {
      label: "Twitter",
      icon: Twitter,
      url: "https://twitter.com/your-profile",
    }, // Replace with actual URL
    { label: "Email", icon: Mail, url: "mailto:support@chainfinity.com" },
  ];

  return (
    <footer className="w-full border-t border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 mt-auto">
      <div className="container max-w-screen-2xl py-8 px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand Info */}
          <div className="flex flex-col items-center md:items-start">
            <Link href="/" className="mb-2">
              <span className="font-bold text-xl bg-clip-text text-transparent bg-gradient-to-r from-indigo-500 to-cyan-500 dark:from-indigo-400 dark:to-cyan-400">
                ChainFinity
              </span>
            </Link>
            <p className="text-sm text-muted-foreground text-center md:text-left">
              Empowering decentralized finance with AI-driven insights.
            </p>
          </div>

          {/* Quick Links */}
          <div className="flex flex-col items-center md:items-start">
            <h3 className="text-sm font-semibold text-foreground mb-3">
              Quick Links
            </h3>
            <ul className="space-y-2">
              {quickLinks.map((link) => (
                <li key={link.path}>
                  <Link
                    href={link.path}
                    className="text-sm text-muted-foreground hover:text-primary transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Social/Contact Links */}
          <div className="flex flex-col items-center md:items-start">
            <h3 className="text-sm font-semibold text-foreground mb-3">
              Connect
            </h3>
            <div className="flex space-x-4">
              {socialLinks.map((link) => (
                <a
                  key={link.label}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={link.label}
                  className="text-muted-foreground hover:text-primary transition-colors"
                >
                  <link.icon className="h-5 w-5" />
                </a>
              ))}
            </div>
            {/* Optional: Add email directly if preferred */}
            {/* <p className="text-sm text-muted-foreground mt-3">support@chainfinity.com</p> */}
          </div>
        </div>

        <Separator className="my-6" />

        <div className="text-center text-xs text-muted-foreground">
          © {currentYear} ChainFinity. All rights reserved.
        </div>
      </div>
    </footer>
  );
}

export default Footer;
