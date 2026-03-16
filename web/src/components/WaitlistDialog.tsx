import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { CheckCircle2 } from "lucide-react";

interface WaitlistDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const WaitlistDialog = ({ open, onOpenChange }: WaitlistDialogProps) => {
  const [submitted, setSubmitted] = useState(false);
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!consent) return;

    setLoading(true);
    const form = e.currentTarget;
    const data = new FormData(form);

    const fullName = data.get("fullName") as string;
    const businessName = data.get("businessName") as string;
    const whatsapp = data.get("whatsapp") as string;
    const businessType = data.get("businessType") as string;
    const email = data.get("email") as string;

    const subject = encodeURIComponent("TONIWTPPay Waitlist Signup");
    const body = encodeURIComponent(
      `New Waitlist Signup:\n\nFull Name: ${fullName}\nBusiness Name: ${businessName}\nWhatsApp Number: ${whatsapp}\nBusiness Type: ${businessType || "N/A"}\nEmail: ${email || "N/A"}`
    );

    window.open(`mailto:support@tonihub.net?subject=${subject}&body=${body}`, "_blank");

    setLoading(false);
    setSubmitted(true);
  };

  const handleClose = (value: boolean) => {
    onOpenChange(value);
    if (!value) {
      setTimeout(() => {
        setSubmitted(false);
        setConsent(false);
      }, 300);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="mx-auto max-w-md">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold">
            {submitted ? "You're on the list! 🎉" : "Join the Waitlist"}
          </DialogTitle>
          <DialogDescription>
            {submitted
              ? ""
              : "Be among the first to use TONIWTPPay. We'll reach out on WhatsApp with early access."}
          </DialogDescription>
        </DialogHeader>

        {submitted ? (
          <div className="flex flex-col items-center gap-4 py-6 text-center">
            <CheckCircle2 className="h-12 w-12 text-primary" />
            <p className="text-base font-medium text-foreground">
              Thanks! We'll reach out soon on WhatsApp with early access to TONIWTPPay.
            </p>
            <Button onClick={() => handleClose(false)} className="mt-2 w-full">
              Close
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="fullName">Full Name *</Label>
              <Input id="fullName" name="fullName" placeholder="Jane Uwimana" required />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="businessName">Business Name *</Label>
              <Input id="businessName" name="businessName" placeholder="Uwimana Boutique" required />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="whatsapp">WhatsApp Number *</Label>
              <Input id="whatsapp" name="whatsapp" type="tel" placeholder="+250 7XX XXX XXX" required />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="businessType">Business Type (optional)</Label>
              <Input id="businessType" name="businessType" placeholder="e.g. Restaurant, Retail" />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="email">Email (optional)</Label>
              <Input id="email" name="email" type="email" placeholder="jane@example.com" />
            </div>

            <div className="flex items-start gap-2">
              <Checkbox
                id="consent"
                checked={consent}
                onCheckedChange={(v) => setConsent(v === true)}
              />
              <Label htmlFor="consent" className="text-xs leading-snug text-muted-foreground">
                I agree to be contacted on WhatsApp and email about TONIWTPPay early access and updates.
              </Label>
            </div>

            <Button type="submit" disabled={!consent || loading} className="w-full">
              {loading ? "Submitting…" : "Join Waitlist"}
            </Button>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default WaitlistDialog;
