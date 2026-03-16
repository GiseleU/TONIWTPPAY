// import { useState } from "react";
// import { Menu, X } from "lucide-react";
// import ThemeToggle from "./ThemeToggle";

// const navLinks = [
//   { label: "Features", href: "#features" },
//   { label: "Pricing", href: "#pricing" },
//   { label: "Contact", href: "#contact" },
// ];

// const Header = () => {
//   const [open, setOpen] = useState(false);

//   return (
//     <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
//       <div className="container flex h-16 items-center justify-between">
//         <a href="/" className="text-xl font-bold text-primary">
//           Toni<span className="text-foreground">WtpPay</span>
//         </a>

//         <nav className="hidden items-center gap-6 md:flex">
//           {navLinks.map((l) => (
//             <a key={l.href} href={l.href} className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
//               {l.label}
//             </a>
//           ))}
//           <ThemeToggle />
//           <a href="#pricing" className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90">
//             Join Waitlist
//           </a>
//         </nav>

//         <div className="flex items-center gap-2 md:hidden">
//           <ThemeToggle />
//           <button onClick={() => setOpen(!open)} aria-label="Menu" className="p-2">
//             {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
//           </button>
//         </div>
//       </div>

//       {open && (
//         <nav className="border-t border-border bg-background px-4 pb-4 md:hidden">
//           {navLinks.map((l) => (
//             <a key={l.href} href={l.href} onClick={() => setOpen(false)} className="block py-3 text-sm font-medium text-muted-foreground">
//               {l.label}
//             </a>
//           ))}
//           <a href="#pricing" onClick={() => setOpen(false)} className="mt-2 block rounded-lg bg-primary px-4 py-2 text-center text-sm font-medium text-primary-foreground">
//             Join Waitlist
//           </a>
//         </nav>
//       )}
//     </header>
//   );
// };

// export default Header;


import { useState } from "react";
import { Menu, X } from "lucide-react";
import ThemeToggle from "./ThemeToggle";
import WaitlistDialog from "./WaitlistDialog";

const navLinks = [
  { label: "Features", href: "#features" },
  { label: "Pricing", href: "#pricing" },
  { label: "Contact", href: "#contact" },
];

const Header = () => {
  const [open, setOpen] = useState(false);
  const [waitlistOpen, setWaitlistOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
      <div className="container flex h-16 items-center justify-between">
        <a href="/" className="text-xl font-bold text-primary">
          TONI<span className="text-foreground">WTPPay</span>
        </a>

        <nav className="hidden items-center gap-6 md:flex">
          {navLinks.map((l) => (
            <a key={l.href} href={l.href} className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
              {l.label}
            </a>
          ))}
          <ThemeToggle />
          <button onClick={() => setWaitlistOpen(true)} className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90">
            Join Waitlist
          </button>
        </nav>

        <div className="flex items-center gap-2 md:hidden">
          <ThemeToggle />
          <button onClick={() => setOpen(!open)} aria-label="Menu" className="p-2">
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {open && (
        <nav className="border-t border-border bg-background px-4 pb-4 md:hidden">
          {navLinks.map((l) => (
            <a key={l.href} href={l.href} onClick={() => setOpen(false)} className="block py-3 text-sm font-medium text-muted-foreground">
              {l.label}
            </a>
          ))}
          <button onClick={() => { setOpen(false); setWaitlistOpen(true); }} className="mt-2 block w-full rounded-lg bg-primary px-4 py-2 text-center text-sm font-medium text-primary-foreground">
            Join Waitlist
          </button>
        </nav>
      )}
      <WaitlistDialog open={waitlistOpen} onOpenChange={setWaitlistOpen} />
    </header>
  );
};

export default Header;
