const Footer = () => (
  <footer className="border-t border-border bg-background py-8">
    <div className="container flex flex-col items-center gap-6 text-sm text-muted-foreground">
      {/* Hub Teaser */}
      {/* <p className="rounded-full border border-accent/30 bg-accent/5 px-5 py-2 text-center text-xs font-medium">
        ToniHub — Coming 2025: CRM, Inventory, POS, Analytics. One login for all.
      </p> */}

      <nav className="flex flex-wrap justify-center gap-6">
        <a href="/" className="hover:text-foreground">Home</a>
        <a href="#features" className="hover:text-foreground">Features</a>
        <a href="#pricing" className="hover:text-foreground">Pricing</a>
        <a href="/privacy" className="hover:text-foreground">Privacy Policy</a>
        <a href="#contact" className="hover:text-foreground">Contact</a>
      </nav>

      <p>© 2026 ToniHub. All rights reserved.</p>
    </div>
  </footer>
);

export default Footer;
